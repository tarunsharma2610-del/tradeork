# Tradeork — Project Handover

> **Read this first.** This file is the single source of truth for AI agents
> working on this repo. It explains what the project is, what has been done,
> the current phase, and the next step — so you don't have to re-discover the
> codebase from scratch.
>
> **Keep this file updated.** Whenever a task changes the project (new feature,
> new phase, new endpoint, config change, schema change), update the relevant
> section (Current status, Done, Next) and commit it in the same change.

## Change workflow (mandatory for every agent)

Follow this on **every** task, not just at phase boundaries:

1. Make the code change.
2. Verify: run the backend + frontend checks listed in "Verification commands".
3. **Update HANDOVER.md** (and README.md when user-facing) if anything changed:
   Current status, What has been done, Next step, or this section. If behavior,
   config, schema, API, or file layout changed, this file MUST be touched.
4. Commit code + docs **together** in one commit, then push to GitHub.

> The commit is only half the job: a commit without its HANDOVER update is a
> clean record of a stale document. Never push a behavior change without
> updating this file in the same commit.
>
> Commit often (per change, not per phase) — a phase spans many sessions, and
> the handover must reflect reality at every point, not just at "phase done".

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
│   │   ├── services/            # auth, users, portfolios, paper_engine, live_execution, market_data/upstox/quote_stream, broker/upstox_broker/broker_factory, audit
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

**Phase: 4 — Live execution adapter. Item 1 (BrokerAdapter interface +
Upstox/Mock adapters + factory) and item 2 (portfolio LIVE mode wired to the
adapter) are DONE. Paper engine remains untouched as the source of truth.**

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
| Continue Phase 4 (broker adapter) | `HANDOVER.md` → `backend/app/services/broker.py` → `backend/app/services/upstox_broker.py` → `backend/app/services/broker_factory.py` → `backend/app/services/live_execution.py` → `backend/app/api/v1/endpoints/trading.py` → `backend/tests/test_live_execution.py` |
| Understand the paper engine | `backend/app/services/paper_engine.py` → `backend/app/domain/enums.py` → `backend/app/models/order.py` + `position.py` + `trade.py` → `backend/tests/test_paper_engine.py` |
| Add/change an API endpoint | `backend/app/api/v1/endpoints/*.py` (the matching one) → `backend/app/api/v1/router.py` → `backend/app/schemas/*.py` → matching test in `backend/tests/` |
| Work on frontend | `frontend/src/lib/api.ts` → `frontend/src/app/dashboard/page.tsx` → the relevant `frontend/src/components/*.tsx` → `frontend/src/lib/use-market-stream.ts` |
| Change auth/session | `backend/app/services/auth.py` → `backend/app/api/v1/endpoints/auth.py` → `backend/app/core/security.py` → `frontend/src/lib/auth.tsx` |
| Change market data | `backend/app/services/market_data.py` → `provider_factory.py` → `quote_stream.py` → `upstox.py` → `backend/app/api/v1/endpoints/market.py` |
| DB schema change | `backend/app/models/<entity>.py` → `backend/alembic/versions/` (next revision) → `backend/app/repositories/<entity>.py` → add a test |

### File map (one line each)

**Backend services** (`backend/app/services/`)
- `paper_engine.py` (423) — THE core: order placement, fills, matcher, positions, summary. Read for any trading change.
- `live_execution.py` (~230) — LIVE path: routes orders to a `BrokerAdapter`, books broker fills into the paper ledger.
- `market_data.py` (188) — quote fetching/caching via provider abstraction.
- `broker.py` (~110) — `BrokerAdapter` ABC + DTOs + `MockBrokerAdapter` (LIVE execution seam).
- `upstox_broker.py` (~150) — Upstox v2 order placement adapter (`place`/`cancel`/`status`).
- `broker_factory.py` (~25) — picks mock vs upstox from `BROKER_ADAPTER`.
- `auth.py` (137) — register/login/refresh/logout logic.
- `quote_stream.py` (136) — WebSocket quote streaming.
- `upstox.py` (113) — Upstox REST provider (live quotes).
- `provider_factory.py` (33) — picks mock vs upstox from `MARKET_DATA_PROVIDER`.
- `portfolios.py` (79), `instruments.py` (38), `users.py` (20), `audit.py` (36).

**Backend API** (`backend/app/api/v1/endpoints/`)
- `trading.py` (115) — Phase 3+4 endpoints (orders/positions/summary; dispatch by portfolio execution mode).
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

### Phase 4 — Live execution adapter: `BrokerAdapter` interface (item 1)
- New `app/services/broker.py`: `BrokerAdapter` ABC (place/cancel/status),
  `BrokerOrderRequest`/`BrokerOrderResult` DTOs, `BrokerAPIError`,
  `MockBrokerAdapter` (`is_mock=true`; MARKET fills, LIMIT rests pending).
- New `app/services/upstox_broker.py`: `UpstoxBrokerAdapter`
  (`is_mock=false`) calling Upstox v2 `/order/place`, `/order/cancel`,
  `/order/details`; status mapped to paper vocabulary
  (`complete`→`filled`). LIMIT orders require a limit price.
- New `app/services/broker_factory.py`: `get_broker()` selects mock vs upstox
  from `BROKER_ADAPTER`, failing safe to mock when Upstox credentials are
  missing (mirrors `provider_factory`).
- Config: `BROKER_ADAPTER` (default `mock`), `UPSTOX_BROKER_PRODUCT`
  (default `D`); validator added. `.env.example` updated.
- **Strict PAPER/LIVE separation preserved**: `paper_engine.py` is untouched
  and never calls a broker. The adapter is the execution seam for a future
  live mode; it is currently exercised only via tests.
- Tests: 19 new in `tests/test_broker.py` (mock adapter lifecycle, Upstox
  payloads/parsing/error paths via patched `httpx.AsyncClient` verbs, factory
  selection/fallback), **93 total passing**; ruff clean; migrations OK.

### Phase 4 — Live execution path wired to the broker (item 2)
- New `ExecutionMode` enum (`paper`/`live`); config `LIVE_EXECUTION_ENABLED`
  (default false) is the master switch for live portfolios.
- Migration `0004`: `portfolios.execution_mode` (default `paper`),
  `orders.execution_mode` (default `paper`), `orders.broker_order_id` —
  SQLite-compatible.
- Portfolio create/update accepts `execution_mode`; creating/switching a live
  portfolio is rejected unless `LIVE_EXECUTION_ENABLED=true`.
- New `app/services/live_execution.py`: `LiveExecutionService` routes
  place/cancel/refresh to a `BrokerAdapter` and **books broker-reported fills
  into the paper ledger** (cash, positions, trades) so the user's displayed
  book stays the source of truth. Rejects live orders when the resolved
  broker adapter is `is_mock=true`.
- `trading.py` dispatches by `portfolio.execution_mode` for place/cancel;
  live-only `POST /portfolios/{id}/orders/{order_id}/refresh` syncs broker
  state. Paper matcher now skips live orders.
- `MockBrokerAdapter` gained a `fill_price` so MARKET fills can be booked.
- Frontend `api.ts` types extended with `execution_mode`/`broker_order_id`.
- Tests: 13 new in `tests/test_live_execution.py` (service + API flows,
  ledger booking, gates, matcher skip, ownership), **106 total passing**;
  ruff clean; migration up/down/up OK; frontend typecheck/lint/build green.

## Verification commands

```bash
# Backend (from backend/)
cd backend
ruff check app tests
python3 -m pytest -q          # expect 106 passed
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

**Phase 4: Live execution adapter.** Items 1–2 done: `BrokerAdapter` +
Upstox/Mock + factory, and a portfolio-level LIVE mode wired to it (orders
route through the adapter, fills mirror into the paper ledger). Remaining open
items, in suggested order:

1. **Upstox OAuth token refresh** (currently expects long-lived token).
2. **Order book / slippage / brokerage-fee model** for paper fills (currently
   fills at last price with no fees).
3. **Margin/leverage checks** for shorts and leveraged products.
4. Real **instrument-master sync** from a broker/exchange feed (catalog is
   currently static seeded data); Upstox order placement needs account-scoped
   instrument tokens resolved from it.
5. **Live order-status sync automation** — the live `refresh` endpoint exists
   but nothing polls it yet; a background job or WebSocket push could keep
   live orders in sync without manual refresh.
6. Later phases from README: strategies, backtesting, news, AI, notifications.

If the user instead asks for a different feature, treat that as the next step
and update this file accordingly.

## Conventions & gotchas

- Strict PAPER/LIVE separation: paper engine must never call broker order APIs.
- Live execution is gated by `LIVE_EXECUTION_ENABLED` (default false) AND a
  non-mock broker adapter; a live portfolio/order is rejected otherwise.
- Live fills are mirrored into the paper ledger (cash/positions/trades) so the
  displayed book stays the source of truth for the user.
- Money uses `Decimal` (precision 18, scale 2), never floats, in the backend.
- Tenant ownership enforced in service layer via `current_user.id` — never trust
  portfolio ids from the request body alone.
- Frontend reverse proxy: `/api/*` → backend in `next.config.*` / dev server.
- `.env.example` is the only env template; never commit real secrets.
- Test fixtures in `backend/tests/conftest.py` disable `PAPER_MATCHER_ENABLED`.
- StarletteDeprecationWarning (httpx/TestClient) is pre-existing and harmless.
- Git: repo has no submodules; commit on `main`; always keep `git status` clean.
