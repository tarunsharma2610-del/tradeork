# Tradeork

Multi-user SaaS paper-trading platform for Indian markets (NSE, BSE, MCX).
Architected so the trading engine can later support real broker execution
(Upstox first, then Zerodha/Groww) with strict PAPER/LIVE separation.

**Status: Phase 1 — Portfolios, instruments + market data foundation.**

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
  - Market data foundation: provider abstraction + clearly-labelled mock
    provider (`is_mock: true`, `source: "mock"`), Redis-cached quotes (TTL 2s)
    that degrade gracefully to provider-only
  - Seed script (`python -m app.seed`) for the reference instrument catalog
  - Audit logging for security-relevant events
  - Health endpoint reporting DB + Redis status
  - Typed request/response models, consistent error responses, versioned API (`/api/v1`)
- **Frontend** (`frontend/`, Next.js 15 + TypeScript + Tailwind + shadcn/ui)
  - Landing page, login, register, dashboard
  - Dashboard: account card, portfolios section (create/delete), market quotes
    card (live simulated quotes, mock-labelled), system status
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
│   │   ├── services/       # business logic (portfolios, instruments, market data)
│   │   └── repositories/   # data access
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/            # pages (landing, login, register, dashboard)
│       ├── components/     # shadcn/ui primitives + theme
│       └── lib/            # api client, auth context
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
- No broker credentials are stored or handled anywhere yet.
- Portfolio ownership is enforced server-side (never trusted from the request
  body); a user cannot read or mutate another tenant's portfolios.
- All market data is simulated and explicitly labelled (`is_mock: true`); the
  provider abstraction ensures real feeds cannot be mistaken for mock data.

## Known limitations / deferred to later phases

- Docker cannot be exercised in the current sandbox; the compose file and
  Dockerfiles are authored and YAML-validated but not yet built here.
- Local verification used SQLite; the CI pipeline runs the full Postgres + Redis
  migration and test path.
- Auth session is in-memory on the frontend: a page reload loses the access
  token (refresh-cookie flow is implemented server-side and will be wired up).
- No email verification, MFA/2FA, password reset yet (skeleton only).
- The instrument catalog is static reference data seeded into the DB; real
  instrument-master synchronisation from a broker/exchange feed is deferred.
- Market quotes are synthetic (`MockMarketDataProvider`); no real tick data or
  WebSocket streaming yet. Quotes are cached 2s in Redis.
- Orders, positions, P&L, strategies, backtesting, broker adapters, news, AI
  and notifications are the subject of later phases.
- Rate limiting falls back to in-memory when Redis is unreachable (single-node
  only; not for multi-instance deployments).

## Manual testing checklist (Phase 1)

1. Register a new account → lands on dashboard, shows account details.
2. Dashboard → **Portfolios**: create one (name + capital), it appears in the list.
3. Create a second portfolio with the same name → friendly 409 error shown.
4. Dashboard → **Market quotes**: default `RELIANCE,TCS,NIFTY` loads mock quotes
   (each row tagged `mock`); change symbols and refresh.
5. Request an unknown symbol (e.g. `ZZZZ`) → friendly 404 error shown.
6. Delete a portfolio → it disappears from the list.
7. Sign out → returns to login; login again → portfolios still listed.
8. Direct hit on `/api/v1/portfolios` or `/api/v1/market/quotes` without a token → 401.
9. With Docker: `docker compose up --build` then repeat the above via `http://localhost`.
10. Confirm `/docs` renders the OpenAPI schema for the new endpoints.
