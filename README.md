# Tradeork

Multi-user SaaS paper-trading platform for Indian markets (NSE, BSE, MCX).
Architected so the trading engine can later support real broker execution
(Upstox first, then Zerodha/Groww) with strict PAPER/LIVE separation.

**Status: Phase 2 — Live market data via WebSocket streaming (Upstox provider).**

## What is implemented

- **Backend** (`backend/`, Python 3.11 + FastAPI)
  - Modular architecture: `core` / `api` / `models` / `schemas` / `services` / `repositories`
  - Auth skeleton: registration, login, refresh-token rotation, logout
    - Argon2id password hashing
    - Short-lived access JWT (Authorization header) + opaque httpOnly refresh cookie
    - Refresh tokens stored hashed, revocable, rotation on every refresh
    - Per-IP rate limiting on auth endpoints (Redis-backed, in-memory fallback)
  - SQLAlchemy 2.0 models + Alembic migrations (`users`, `refresh_tokens`,
    `audit_logs`, `portfolios`, `instruments`)
  - Portfolios: tenant-scoped CRUD (list/create/get/update/delete), unique name
    per user, Decimal capital, ownership enforced in the service layer
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
    confirmation), market quotes card (WebSocket streaming with automatic
    polling fallback, live/mock badge, per-symbol source tag, price sparkline,
    instrument-catalog search to add symbols), dynamic "Data mode" stat that
    reflects the actual feed, system status
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
│   │   │                   #   upstox provider, provider factory, quote stream)
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
- No broker credentials are stored or handled anywhere yet; Upstox credentials
  are provided via environment configuration only.
- Portfolio ownership is enforced server-side (never trusted from the request
  body); a user cannot read or mutate another tenant's portfolios.
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
- Orders, positions, P&L, strategies, backtesting, broker adapters, news, AI
  and notifications are the subject of later phases.
- Rate limiting falls back to in-memory when Redis is unreachable (single-node
  only; not for multi-instance deployments).

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
