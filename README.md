# Tradeork

Multi-user SaaS paper-trading platform for Indian markets (NSE, BSE, MCX).
Architected so the trading engine can later support real broker execution
(Upstox first, then Zerodha/Groww) with strict PAPER/LIVE separation.

**Status: Phase 4 — Live execution adapter + portfolio LIVE mode. Paper engine
remains the source of truth. A Settings page exposes the per-portfolio
paper/live switch.**

## What is implemented

- **Backend** (`backend/`, Python 3.11 + FastAPI)
  - Modular architecture: `core` / `api` / `models` / `schemas` / `services` / `repositories`
  - Auth skeleton: registration, login, refresh-token rotation, logout
    - Argon2id password hashing
    - Short-lived access JWT (Authorization header) + opaque httpOnly refresh cookie
    - Refresh tokens stored hashed, revocable, rotation on every refresh
    - Per-IP rate limiting on auth endpoints (Redis-backed, in-memory fallback)
  - SQLAlchemy 2.0 models + Alembic migrations (`users`, `refresh_tokens`,
    `audit_logs`, `portfolios`, `instruments`, `orders`, `positions`, `trades`)
  - Portfolios: tenant-scoped CRUD (list/create/get/update/delete), unique name
    per user, Decimal capital, ownership enforced in the service layer;
    `cash` tracks the live paper-trading balance
  - **Paper-trading engine** (`PaperOrderEngine`): MARKET and LIMIT order
    placement, immediate fill for marketable orders, background matcher that
    fills resting LIMIT orders when the market crosses, order cancellation,
    position tracking (signed quantity, VWAP average price, realized/unrealized
    P&L), and a portfolio summary (cash, equity, P&L). Execution is strictly
    paper-only — no broker order APIs are invoked.
  - **Broker execution adapter** (`BrokerAdapter` interface with mock and
    Upstox implementations): `place_order`/`cancel_order`/`get_order_status`
    against Upstox v2 order endpoints, selected by `BROKER_ADAPTER` config
    (safe fallback to the labelled mock adapter). This is the LIVE side of the
    PAPER/LIVE separation: the paper engine never calls a broker.
  - **Portfolio LIVE mode**: portfolios can be created/switched to
    `execution_mode=live` (gated by `LIVE_EXECUTION_ENABLED`). Orders on a
    live portfolio are routed through the broker adapter and the
    broker-reported fills are mirrored into the paper ledger, so the user's
    displayed book stays the source of truth. A live-only
    `POST /portfolios/{id}/orders/{order_id}/refresh` syncs broker state.
  - Instruments: reference catalog (NSE/BSE/MCX, equity/futures/options) with
    search (symbol/name, exchange, instrument type) and natural-key dedupe
  - Market data: provider abstraction + clearly-labelled mock provider
    (`is_mock: true`, `source: "mock"`), Redis-cached quotes (TTL 2s)
    that degrade gracefully to provider-only
  - **Live market data**: `UpstoxMarketDataProvider` (`is_mock: false`,
    `source: "upstox"`) via Upstox v2 REST quotes; provider selected by
    `MARKET_DATA_PROVIDER` config, with safe mock fallback when live
    credentials are missing
  - **WebSocket quote streaming** (`/api/v1/market/ws`): authenticated via
    access-token query param, push interval from `MARKET_DATA_POLL_INTERVAL`,
    supports dynamic subscribe messages and a client that falls back to polling
  - Seed script (`python -m app.seed`) for the reference instrument catalog
  - Audit logging for security-relevant events
  - Health endpoint reporting DB + Redis status
  - Typed request/response models, consistent error responses, versioned API (`/api/v1`)
- **Frontend** (`frontend/`, Next.js 15 + TypeScript + Tailwind + shadcn/ui)
  - Landing page, login, register, dashboard
  - Dashboard: account card, portfolios section (create/delete with inline
    confirmation, cash balance per portfolio), market quotes card (WebSocket
    streaming with automatic polling fallback, live/mock badge, per-symbol
    source tag, price sparkline, instrument-catalog search to add symbols),
    dynamic "Data mode" stat that reflects the actual feed, system status
  - Dashboard paper-trading panel: trade ticket (instrument search, BUY/SELL,
    MARKET/LIMIT, quantity, limit price), positions table with unrealized P&L,
    order list with cancel, and a live summary (cash, equity, realized/
    unrealized P&L)
  - Settings page (`/settings`): per-portfolio **Paper/Live** trading-mode
    switch (confirmation required when switching to live; live gated
    server-side by `LIVE_EXECUTION_ENABLED`) plus a read-only Execution card
    showing the configured broker adapter, market-data provider and live
    availability; linked from the dashboard header
  - **Per-user broker connections** (Settings → "Broker connection"): users
    add their own Upstox API credentials, stored **encrypted at rest**
    (Fernet keyed off `SECRET_KEY`) and never returned — only masked previews
    (`****abcd`). CRUD API under `/api/v1/settings/broker` (tenant-scoped,
    max 5 connections/user). Live portfolios resolve the executing broker
    adapter from the current user's stored connection first
    (`broker_factory.get_broker_for_user`), falling back to the
    server-configured `BROKER_ADAPTER`.
  - Reverse proxy: `/api/*` → backend (no CORS issues, single entry point)
  - Light + dark themes, responsive layout
- **Deployment**
  - Dockerfiles for backend and frontend
  - `docker-compose.yml`: PostgreSQL 16, Redis 7, backend, frontend, Nginx
  - Nginx terminates at port 80 and routes `/` → frontend, `/api/` → backend (WebSocket upgrade ready)
- **CI** (`.github/workflows/ci.yml`)
  - Backend: ruff lint, pytest against real Postgres + Redis, migration up/down/up
  - Frontend: typecheck, eslint, production build

## Repository layout

```
.
├── backend/
│   ├── alembic/            # migrations
│   ├── app/
│   │   ├── core/           # config, database, redis, security, rate limit
│   │   ├── api/v1/         # routers + endpoints (auth, users, health, portfolios, instruments, market)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # business logic (portfolios, instruments, market data,
│   │   │                   #   upstox provider, provider factory, quote stream,
│   │   │                   #   broker adapters + live_execution: broker.py, upstox_broker.py,
│   │   │                   #   broker_factory.py, live_execution.py)
│   │   └── repositories/   # data access
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/            # pages (landing, login, register, dashboard)
│       ├── components/     # shadcn/ui primitives + theme
│       └── lib/            # api client, auth context, use-market-stream hook
├── nginx/nginx.conf
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Run it

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env          # adjust SECRET_KEY in production
docker compose up --build
```

- Frontend + API: `http://localhost` (Nginx routes `/api/*` to the backend)
- API docs: `http://localhost/api/v1/openapi.json`
- FastAPI docs (direct): `http://localhost:8000/docs`
- PostgreSQL on `5432`, Redis on `6379`

Migrations run automatically on backend container start (`alembic upgrade head`).

The instrument catalog is reference data only and is never fetched from a
broker. Seed it once (or re-run to update non-destructively):

```bash
cd backend
python -m app.seed                 # all exchanges
python -m app.seed --exchange NSE  # single exchange
```

### Option B — Local development

```bash
# 1. Start infrastructure
docker compose up db redis

# 2. Backend (http://localhost:8000)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend (http://localhost:3000)
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

The frontend proxies `/api/*` to the backend so you can always use
`http://localhost:3000/api/v1/...`.

## Market data providers

Quotes flow through a provider abstraction. Every quote carries
`is_mock` and `source`, so simulated data can never be mistaken for a
live feed.

| Provider | `is_mock` | `source` | Config |
|----------|-----------|----------|--------|
| Mock (default) | `true` | `mock` | `MARKET_DATA_PROVIDER=mock` |
| Upstox (live) | `false` | `upstox` | `MARKET_DATA_PROVIDER=upstox` + Upstox credentials |

To enable live data:

```bash
# backend/.env (or docker-compose environment)
MARKET_DATA_PROVIDER=upstox
UPSTOX_API_KEY=your-app-key
UPSTOX_ACCESS_TOKEN=your-long-lived-access-token
UPSTOX_BASE_URL=https://api.upstox.com/v2
```

If `upstox` is selected but the credentials are missing, the service logs a
warning and **fails safe to the mock provider** (still labelled `is_mock:
true`) rather than crashing or mislabelling data.

### WebSocket streaming

Authenticated clients can subscribe to a live quote stream instead of polling:

```
GET /api/v1/market/ws?token=<access JWT>&symbols=RELIANCE,TCS&exchange=NSE
```

- The browser cannot set headers on a WebSocket handshake, so auth is passed
  as a query parameter; the server validates it like any other access token.
- Push interval follows `MARKET_DATA_POLL_INTERVAL` (default 2s).
- Re-subscribe at any time by sending `{"action": "subscribe", "symbols":
  [...], "exchange": "NSE"}`; unknown symbols are reported back as an
  `error` frame (`code: "unknown_symbols"`) instead of being silently dropped.
- The dashboard quotes card opens this stream automatically and transparently
  falls back to REST polling (every 3s) if the socket cannot be established.

## Verify

```bash
# Backend
cd backend && pytest && ruff check app tests

# Frontend
cd frontend && npm run typecheck && npm run lint && npm run build
```

## Security notes

- Access tokens are returned in the response body and must be kept in memory by the SPA
  (they are not stored in `localStorage`/`sessionStorage`).
- Refresh tokens are set as `httpOnly` cookies; `Secure` is enabled when
  `ENVIRONMENT=production`.
- `SECRET_KEY` is validated at startup: production refuses the placeholder value
  and any key shorter than 32 characters.
- CSRF: the API is bearer-token based (no cookie-authenticated state-changing
  requests), so CSRF protection applies once cookie-based flows are introduced.
- Per-user broker credentials (Upstox access token / API key) are stored
  **encrypted at rest** using Fernet keyed deterministically off `SECRET_KEY`
  (see `backend/app/core/security.py`). They are never returned by any API —
  only masked previews (`****abcd`). Rotating `SECRET_KEY` invalidates stored
  broker secrets; the user must re-enter them.
- No broker credentials are stored or handled anywhere except the encrypted
  `broker_connections` store; server-side Upstox credentials are provided via
  environment configuration only.
- Portfolio ownership is enforced server-side (never trusted from the request
  body); a user cannot read or mutate another tenant's portfolios.
- Settings: `GET /settings/execution` (authenticated) exposes non-secret
  execution config (broker adapter, market-data provider, whether live
  portfolios are enabled) for the Settings UI — credentials are never
  returned.
- All market data is labelled with `is_mock`/`source`; the provider abstraction
  ensures real feeds cannot be mistaken for mock data. The default provider is
  mock; live Upstox data activates only when explicitly configured.

## Known limitations / deferred to later phases

- Docker cannot be exercised in the current sandbox; the compose file and
  Dockerfiles are authored and YAML-validated but not yet built here.
- Local verification used SQLite; the CI pipeline runs the full Postgres + Redis
  migration and test path.
- Auth session is kept in memory on the frontend, restored on reload via the
  httpOnly refresh cookie.
- No email verification, MFA/2FA, password reset yet (skeleton only).
- The instrument catalog is static reference data seeded into the DB; real
  instrument-master synchronisation from a broker/exchange feed is deferred.
- The default provider is synthetic (`MockMarketDataProvider`); real tick data
  via a broker WebSocket feed (Upstox/other) and Upstox OAuth token refresh are
  deferred. Quotes are cached 2s in Redis and streamed over our own WebSocket.
- The Upstox access token is expected to be long-lived; automatic re-auth on
  expiry is not implemented yet.
- Paper execution fills against the quote feed's last price; there is no order
  book, slippage, or fees model yet.
- Short selling is allowed without a margin/leverage check (by design for
  paper trading).
- Live order placement is wired (`BROKER_ADAPTER=upstox` + credentials +
  `LIVE_EXECUTION_ENABLED=true` + a live portfolio), but live order-status
  sync is manual (`POST .../orders/{id}/refresh`) — no background sync yet.
- Strategies, backtesting, news, AI
  and notifications are the subject of later phases. The user has also
  requested a per-portfolio **strategies bar** (manually add/edit strategies)
  and an **autotrade** toggle in Settings so strategies can auto-place orders
  through the chosen execution mode (paper/live); see `HANDOVER.md` "Next step".
  The Settings page, paper/live switch and per-user broker connections are
  implemented; the strategies bar (backend CRUD + dashboard panel) is
  implemented but no strategy engine/signals exist yet, and the autotrade flag
  is not.
- Rate limiting falls back to in-memory when Redis is unreachable (single-node
  only; not for multi-instance deployments).

## Deploy to Oracle Cloud (final destination)

**After the project is feature-complete, it MUST be uploaded and run on the
user's Oracle Cloud free-tier Ubuntu server.** This is the required target
environment for the finished product — local sandbox and Docker Compose are
only for development/verification.

### Target VM

- Oracle Cloud Free Tier — **Ampere A1 (ARM)**, Ubuntu 22.04/24.04, ≥2 OCPU /
  ≥4 GB RAM.
- In the console's security list / NSG, open **TCP 80** (and 443 if using TLS)
  to `0.0.0.0/0`; keep SSH open for administration.

### Steps

```bash
ssh ubuntu@<PUBLIC_IP>

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu          # re-login after this

# Clone + configure
git clone https://github.com/tarunsharma2610-del/tradeork.git
cd tradeork
cp .env.example .env
# .env: ENVIRONMENT=production, SECRET_KEY=<openssl rand -hex 32>,
#       BACKEND_CORS_ORIGINS=http://<PUBLIC_IP> (or domain)

# Launch
sudo docker compose up -d --build
sudo docker compose ps                  # all 5 services Up/healthy

# Seed instrument catalog once
sudo docker compose exec backend python -m app.seed
```

- Site: `http://<PUBLIC_IP>/` · API docs: `http://<PUBLIC_IP>/api/v1/openapi.json`
- Health: `http://<PUBLIC_IP>/api/v1/health` → `database: ok`, `redis: ok`
  (Healthy — unlike the sandbox, Redis and Postgres run here).
- Updates: `git pull && sudo docker compose up -d --build` (migrations run
  automatically on backend start).
- **Compose gap:** `docker-compose.yml` currently does NOT pass
  `BROKER_ADAPTER` / `LIVE_EXECUTION_ENABLED` / `UPSTOX_BROKER_PRODUCT` to the
  backend container (only market-data provider + Upstox quotes creds). Add
  those env vars to the backend service in `docker-compose.yml` if live
  execution is needed on the server.

## Manual testing checklist (Phase 1)

1. Register a new account → lands on dashboard, shows account details.
2. Dashboard → **Portfolios**: create one (name + capital), it appears in the list.
3. Create a second portfolio with the same name → friendly 409 error shown.
4. Dashboard → **Market quotes**: default `RELIANCE,TCS,NIFTY` loads quotes;
   the badge shows `mock · streaming` when connected over WebSocket (or
   `polling` if the socket falls back). Change symbols and watch them update;
   each row carries a `mock`/`live` tag and a price sparkline.
5. Use the **"Add symbol"** search to pick instruments from the catalog
   (e.g. `HDFCBANK`); the symbol joins the watchlist.
6. Request an unknown symbol (e.g. `ZZZZ`) → REST shows a 404; the WebSocket
   stream instead sends an `unknown_symbols` error frame listing it.
7. Delete a portfolio → it asks for confirmation before removing.
8. Sign out → returns to login; login again → portfolios still listed.
9. Direct hit on `/api/v1/portfolios` or `/api/v1/market/quotes` without a token → 401.
10. With Docker: `docker compose up --build` then repeat the above via `http://localhost`.
11. Confirm `/docs` renders the OpenAPI schema for the new endpoints.
12. With Upstox credentials configured (`MARKET_DATA_PROVIDER=upstox`), the
    quotes card badge switches to `live · streaming`, rows show `live` tags,
    and the dashboard "Data mode" stat reports `Live`.

## Manual testing checklist (Phase 3)

1. On the dashboard, create a portfolio (or use an existing one) — its row now
   also shows the running **cash** balance.
2. **Paper trading** panel → pick the portfolio, search an instrument
   (e.g. `RELIANCE`), choose **BUY / MARKET**, quantity 10 → **Buy market**.
   The order fills immediately; the positions table shows qty 10 and the
   summary's cash drops by the fill cost.
3. Place a **BUY / LIMIT** order priced below the last quote → it stays
   `pending`. When the mock market drifts below the limit, the background
   matcher fills it (refresh to see the status flip to `filled`).
4. **Sell** some/all of the position → realized P&L accrues; closing a position
   sets qty to 0 and cash reflects the proceeds.
5. Open an order list — pending orders expose a cancel action; cancelling
   flips the status to `cancelled` (filled orders cannot be cancelled).
6. Place an order with quantity exceeding available cash → it is `rejected`
   with an "Insufficient cash" reason.
7. Summary row updates: **Cash**, **Equity**, **Realized/Unrealized P&L**
   track your trades; equity returns to initial capital when all positions
   are flat.
8. Confirm `/docs` lists the trading endpoints
   (`/portfolios/{id}/orders`, `/positions`, `/summary`).

## Manual testing checklist (Settings)

1. Log in → the dashboard header shows a **Settings** link → click it.
2. The Settings page loads your portfolios, each with a **Paper/Live** switch.
3. Click **Live** on a portfolio → an inline confirmation appears ("Switch to
   live mode — real orders may be placed?") → cancel leaves it on paper.
4. If `LIVE_EXECUTION_ENABLED` is false (default), the Live button is disabled
   and the page explains live mode is disabled on this server.
5. With `LIVE_EXECUTION_ENABLED=true`, confirm the switch → the portfolio badge
   flips to `live`; the dashboard's trading panel now routes its orders through
   the broker adapter for that portfolio.
6. The Execution card shows the configured broker adapter (Mock/Upstox), market
   data provider, and live availability. No secrets/credentials are displayed.
7. **Broker connection** card: add an Upstox access token (+ optional label and
   API key) → it appears with `****<last4>` masked preview and a `connected`
   badge; the Execution card's broker row now reads `Upstox (your account)`.
8. **Update token** on a connection → the masked preview changes; **Disconnect**
   asks for confirmation → the connection is removed and the Execution card
   falls back to the server-configured adapter.
9. Unauthenticated `GET /api/v1/settings/execution` and
   `GET /api/v1/settings/broker` → 401.
10. Secrets are never returned: the API responses contain only
    `access_token_masked`/`api_key_masked` fields.
