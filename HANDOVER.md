# Tradeork — Project Handover

> **Read this first.** This file is the single source of truth for AI agents
> working on this repo. It explains what the project is, what has been done,
> the current phase, and the next step — so you don't have to re-discover the
> codebase from scratch.
>
> **Keep this file updated.** Whenever a task changes the project (new feature,
> new phase, new endpoint, config change, schema change), update the relevant
> section (Current status, Done, Next) and commit it in the same change.

## What this project is

Tradeork is a **multi-user SaaS paper-trading platform for Indian markets**
(NSE, BSE, MCX). Users register, create paper portfolios with a cash balance,
and trade against (mock or live) market quotes. It is architected so a real
broker execution adapter (Upstox first, then Zerodha/Groww) can be added later
with **strict PAPER/LIVE separation** — the paper engine never calls broker
order APIs.

- Backend: Python 3.11 + FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2.
- Frontend: Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui.
- Deploy: Docker Compose (PostgreSQL 16, Redis 7, backend, frontend, Nginx);
  CI via GitHub Actions.
- Sandbox note: this workspace has no Docker/Postgres/Redis; local verification
  uses SQLite + tests.

## Repository layout

```
.
├── backend/
│   ├── alembic/                 # migrations 0001..0003
│   ├── app/
│   │   ├── api/v1/endpoints/    # auth, users, portfolios, trading, instruments, market, health
│   │   ├── core/                # config, database, redis, security
│   │   ├── domain/              # enums (OrderSide/Type/Status, etc.)
│   │   ├── models/              # User, RefreshToken, AuditLog, Portfolio, Instrument, Order, Position, Trade
│   │   ├── schemas/             # request/response Pydantic models
│   │   ├── services/            # auth, users, portfolios, paper_engine, market_data/upstox/quote_stream, audit
│   │   └── repositories/        # data-access layer per entity
│   └── tests/                   # pytest + ruff (74 tests, all green)
├── frontend/
│   └── src/
│       ├── app/                 # /, /login, /register, /dashboard
│       ├── components/          # dashboard cards, trading panel, instrument search, UI kit
│       └── lib/                 # api client, auth, market stream hook
├── .env.example                 # all env knobs, no real secrets
├── README.md                    # user-facing docs + manual test checklists
└── HANDOVER.md                  # this file
```

## Current status

**Phase: 3 — Paper-trading execution engine (orders, positions, P&L). DONE.**

All backend and frontend checks pass. The last commit is on `main`.

## How to continue WITHOUT burning your token budget

The whole repo is **~7,400 lines** (~3,400 backend, ~1,200 tests, ~2,800
frontend). **Do NOT read everything.** Read only the files your task touches.

- Files are cheap to read (models/schemas/repositories are 20-80 lines each).
  The three "big" files that matter are `paper_engine.py` (423), `seed.py`
  (217), and `trading-panel.tsx` (517).
- Tests are the best spec: for any behaviour question, read the matching test
  file first — it shows exactly how the engine/API is expected to behave.

### Reading plans

| Your task | Files to read (in order) |
|---|---|
| Continue Phase 4 (broker adapter) | `HANDOVER.md` → `backend/app/services/paper_engine.py` → `backend/app/core/config.py` → `backend/app/services/provider_factory.py` → `backend/app/services/upstox.py` → `backend/tests/test_paper_engine.py` |
| Understand the paper engine | `backend/app/services/paper_engine.py` → `backend/app/domain/enums.py` → `backend/app/models/order.py` + `position.py` + `trade.py` → `backend/tests/test_paper_engine.py` |
| Add/change an API endpoint | `backend/app/api/v1/endpoints/*.py` (the matching one) → `backend/app/api/v1/router.py` → `backend/app/schemas/*.py` → matching test in `backend/tests/` |
| Work on frontend | `frontend/src/lib/api.ts` → `frontend/src/app/dashboard/page.tsx` → the relevant `frontend/src/components/*.tsx` → `frontend/src/lib/use-market-stream.ts` |
| Change auth/session | `backend/app/services/auth.py` → `backend/app/api/v1/endpoints/auth.py` → `backend/app/core/security.py` → `frontend/src/lib/auth.tsx` |
| Change market data | `backend/app/services/market_data.py` → `provider_factory.py` → `quote_stream.py` → `upstox.py` → `backend/app/api/v1/endpoints/market.py` |
| DB schema change | `backend/app/models/<entity>.py` → `backend/alembic/versions/` (next revision) → `backend/app/repositories/<entity>.py` → add a test |

### File map (one line each)

**Backend services** (`backend/app/services/`)
- `paper_engine.py` (423) — THE core: order placement, fills, matcher, positions, summary. Read for any trading change.
- `market_data.py` (188) — quote fetching/caching via provider abstraction.
- `auth.py` (137) — register/login/refresh/logout logic.
- `quote_stream.py` (136) — WebSocket quote streaming.
- `upstox.py` (113) — Upstox REST provider (live quotes).
- `provider_factory.py` (33) — picks mock vs upstox from `MARKET_DATA_PROVIDER`.
- `portfolios.py` (79), `instruments.py` (38), `users.py` (20), `audit.py` (36).

**Backend API** (`backend/app/api/v1/endpoints/`)
- `trading.py` (72) — Phase 3 endpoints (orders/positions/summary).
- `portfolios.py` (61), `auth.py` (149), `market.py` (102), `instruments.py` (42), `users.py` (12), `health.py` (34).
- `router.py` (20) — registers all routers.

**Backend core** (`backend/app/core/`)
- `config.py` (94) — all env settings (incl. `PAPER_MATCHER_*`).
- `security.py` (56), `database.py` (23), `redis.py` (20), `rate_limit.py` (88).

**Backend models** (`backend/app/models/`) — `order.py` (71), `position.py` (73), `trade.py` (73), `portfolio.py` (59), `instrument.py` (58), `user.py` (53), `refresh_token.py` (42), `audit_log.py` (38). Each is a plain SQLAlchemy table.

**Backend schemas** (`backend/app/schemas/`) — thin Pydantic DTOs, 15-52 lines each.

**Backend tests** (`backend/tests/`) — read as spec: `test_paper_engine.py` (272), `test_trading_api.py` (188), `test_portfolios.py` (140), `test_market_ws.py` (90), others smaller. `conftest.py` (75) = fixtures; `helpers.py` (29) = `register_user`/`auth_headers`.

**Frontend** (`frontend/src/`)
- `lib/api.ts` (253) — typed API client; every backend call goes through here.
- `lib/auth.tsx` (97), `lib/use-market-stream.ts` (203).
- `components/trading-panel.tsx` (517) — trade ticket + positions/orders UI.
- `components/market-quotes-card.tsx` (300), `portfolios-section.tsx` (196), `instrument-search.tsx` (131), `stat-cards.tsx` (78).
- `app/dashboard/page.tsx` (157) — wires everything; `app/page.tsx` (240) = landing.

### Suggested first steps for a new agent

1. Read this HANDOVER.md (you're here).
2. Run the verification commands below to confirm green baseline (cheap, no reading).
3. Read only the files in the row that matches your task.
4. Never read `seed.py` unless touching the instrument catalog.

## What has been done

### Phase 1 — Foundation & auth (commit `646537e`, `b5374a9`)
- Modular backend architecture (`core`/`api`/`models`/`schemas`/`services`/`repositories`).
- Auth: register, login, refresh-token rotation (opaque httpOnly cookie), logout,
  Argon2id hashing, short-lived access JWT, Redis-backed per-IP rate limiting.
- DB: `users`, `refresh_tokens`, `audit_logs`; Alembic migration `0001`.
- Frontend: landing, login, register; reverse proxy `/api/*` → backend.
- CI: ruff + pytest (Postgres+Redis) and frontend typecheck/lint/build.

### Phase 2 — Market data & portfolios (commit `8664d7b`, `a460e75`, `cb2beef`)
- Portfolios: tenant-scoped CRUD, unique name per user, Decimal capital,
  ownership enforced in service layer; migration `0002`.
- Instruments: reference catalog (NSE/BSE/MCX, equity/futures/options) with
  search + natural-key dedupe; seed via `python -m app.seed`.
- Market data: provider abstraction; `MockMarketDataProvider` (default,
  `is_mock=true`) and `UpstoxMarketDataProvider` (live, `is_mock=false`),
  selected by `MARKET_DATA_PROVIDER`; Redis-cached quotes (TTL 2s).
- WebSocket quote streaming `/api/v1/market/ws` with dynamic subscribe +
  client fallback to polling.
- Frontend: dashboard with account card, portfolios section, market quotes card
  (sparklines, live/mock badges, symbol search), theme toggle.

### Phase 3 — Paper-trading engine (commit `2b6de6a`) — current
- Domain enums `OrderSide` (BUY/SELL), `OrderType` (MARKET/LIMIT),
  `OrderStatus` (pending/partially_filled/filled/cancelled/rejected).
- Models + migration `0003`: `orders`, `positions` (signed qty, VWAP avg_price,
  realized_pnl), `trades`; `portfolios.cash` backfilled from `initial_capital`.
  Migration is SQLite-compatible (guards `ALTER … DROP DEFAULT`).
- `PaperOrderEngine` (`app/services/paper_engine.py`): place order (immediate
  fill for marketable orders, else pending), background matcher loop that fills
  resting LIMIT orders when marketable, cancel, positions, portfolio summary
  (cash, equity, realized/unrealized P&L).
  - Fill price: MARKET → `last_price`; LIMIT → `limit_price` when marketable.
  - Cash check: BUY rejected if cost > cash; shorts allowed (no margin check).
  - Summary: equity = cash + Σ(last_price × signed qty).
- Config: `PAPER_MATCHER_ENABLED` (default true), `PAPER_MATCHER_INTERVAL`
  (default 5.0); matcher started/cancelled in FastAPI lifespan (disabled in
  tests).
- API (all tenant-scoped, under `/api/v1`):
  - `POST /portfolios/{id}/orders` — place order
  - `GET /portfolios/{id}/orders?status=` — list orders
  - `DELETE /portfolios/{id}/orders/{order_id}` — cancel pending order
  - `GET /portfolios/{id}/positions` — positions
  - `GET /portfolios/{id}/summary` — cash/equity/P&L summary
- Frontend: `api.ts` types + methods for orders/positions/summary; new
  `TradingPanel` component (trade ticket, positions table, order list with
  cancel, live summary); portfolio cards show cash.
- Tests: 21 new (engine unit + trading API), **74 total passing**; ruff clean;
  frontend typecheck/lint/build green; migration up/down/up + smoke flow
  verified on SQLite.

## Verification commands

```bash
# Backend (from backend/)
cd backend
ruff check app tests
python3 -m pytest -q          # expect 74 passed
# migration up/down/up on SQLite:
DATABASE_URL=sqlite:////tmp/t.db alembic upgrade head && \
DATABASE_URL=sqlite:////tmp/t.db alembic downgrade base && \
DATABASE_URL=sqlite:////tmp/t.db alembic upgrade head

# Frontend (from frontend/)
cd frontend
npm run typecheck
npm run lint
npm run build
```

Manual flow smoke-tested: register → create portfolio → MARKET order fills →
positions/summary/orders reflect cash, position, P&L.

## Next step

**Phase 4 (proposed): Live execution adapter — wire the paper engine to a real
broker.** Open items and natural candidates, in suggested order:

1. **Upstox order placement adapter** behind a `BrokerAdapter` interface
   (place/cancel/status) with the paper engine staying the source of truth for
   the user — i.e. keep PAPER/LIVE strictly separated.
2. **Upstox OAuth token refresh** (currently expects long-lived token).
3. **Order book / slippage / brokerage-fee model** for paper fills (currently
   fills at last price with no fees).
4. **Margin/leverage checks** for shorts and leveraged products.
5. Real **instrument-master sync** from a broker/exchange feed (catalog is
   currently static seeded data).
6. Later phases from README: strategies, backtesting, news, AI, notifications.

If the user instead asks for a different feature, treat that as the next step
and update this file accordingly.

## Conventions & gotchas

- Strict PAPER/LIVE separation: paper engine must never call broker order APIs.
- Money uses `Decimal` (precision 18, scale 2), never floats, in the backend.
- Tenant ownership enforced in service layer via `current_user.id` — never trust
  portfolio ids from the request body alone.
- Frontend reverse proxy: `/api/*` → backend in `next.config.*` / dev server.
- `.env.example` is the only env template; never commit real secrets.
- Test fixtures in `backend/tests/conftest.py` disable `PAPER_MATCHER_ENABLED`.
- StarletteDeprecationWarning (httpx/TestClient) is pre-existing and harmless.
- Git: repo has no submodules; commit on `main`; always keep `git status` clean.
