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
│   ├── alembic/                 # migrations 0001..0006
│   ├── app/
│   │   ├── api/v1/endpoints/    # auth, users, portfolios, trading, strategies, instruments, market, settings, broker_connections, health
│   │   ├── core/                # config, database, redis, security
│   │   ├── domain/              # enums (OrderSide/Type/Status, ExecutionMode, StrategyType/Status, etc.)
│   │   ├── models/              # User, RefreshToken, AuditLog, Portfolio, Instrument, Order, Position, Trade, Strategy, BrokerConnection
│   │   ├── schemas/             # request/response Pydantic models
│   │   ├── services/            # auth, users, portfolios, strategies, paper_engine, live_execution, market_data/upstox/quote_stream, broker/upstox_broker/broker_factory, audit
│   │   └── repositories/        # data-access layer per entity
│   └── tests/                   # pytest + ruff (119 tests, all green)
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
adapter) are DONE. Settings UI with the paper/live portfolio switch is DONE.
Per-portfolio Strategies CRUD (backend + dashboard panel) is DONE. Per-user
broker connections (Settings → "Add Upstox API") are DONE. Dashboard
discoverability (user-feedback item 4: tabbed dashboard with Trading front and
center + prominent Register entry on login) is DONE. Paper engine
remains untouched as the source of truth.**

All backend and frontend checks pass. The last commit is on `main`.

**Current session note (2026-08-19):** Added the full-stack **Strategies**
feature (user-feedback item 1): `strategies` table (migration `0005`), model +
repository + service + schemas, CRUD API under `/portfolios/{id}/strategies`
(tenant-scoped, duplicate-name 409), and a dashboard **Strategies** panel
(add/edit/deactivate/delete per portfolio).

Also added the full-stack **per-user broker connections** feature
(user-feedback item 3 — "In Settings: option to add API / the broker"):
`broker_connections` table (migration `0006`), model + repository + service +
schemas, CRUD API under `/settings/broker` (tenant-scoped, masked-at-rest
secrets via Fernet keyed off `SECRET_KEY`), a **Broker connection** card on
the Settings page (add / update token / disconnect), and live-execution
resolution through the user's own stored credentials
(`broker_factory.get_broker_for_user`, used by `trading._execution_for`).

**Later same session (user-feedback item 4 — dashboard discoverability):**
Reworked `/dashboard` into a tabbed workspace — **Trading** (default, front
and center), **Portfolios & Quotes**, **Strategies**, **Account**. Panels stay
mounted (CSS `hidden`) so the WebSocket quote feed and "Data mode" stat keep
updating across tab switches. The login page now shows a prominent **"Create a
free account"** button (was a subtle text link) so Register is discoverable.

Backend tests now **132 passing**; frontend typecheck/lint/build green; the
migration chain `0001 → 0006` up/down/up verifies. See "Session 2026-08-19
(Strategies)", "Session 2026-08-19 (Broker connections)" and "Session
2026-08-19 (Dashboard discoverability)" under "What has been done".

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
| **Build Strategies feature** | DONE (2026-08-19): model `backend/app/models/strategy.py`, migration `0005`, repo `repositories/strategies.py`, service `services/strategies.py`, schemas `schemas/strategy.py`, API `api/v1/endpoints/strategies.py` (`/portfolios/{id}/strategies` CRUD), UI `frontend/src/components/strategies-panel.tsx` wired into the dashboard. Strategy engine/signals still NOT built. |
| **Build Settings page (live/paper toggle + broker config)** | DONE (2026-08-19): page at `frontend/src/app/settings/page.tsx`, link in `dashboard-header.tsx`, endpoint `backend/app/api/v1/endpoints/settings.py` (`GET /settings/execution`). Broker token store (per-user) is now DONE — see the next row. |
| **Build per-user broker connections (Settings → add Upstox API)** | DONE (2026-08-19): model `backend/app/models/broker_connection.py`, migration `0006`, repo `backend/app/repositories/broker_connections.py`, service `backend/app/services/broker_connections.py`, schemas `backend/app/schemas/broker_connection.py`, API `backend/app/api/v1/endpoints/broker_connections.py` (`/settings/broker` CRUD), UI in `frontend/src/app/settings/page.tsx` (Broker connection card). Live execution resolves the user's stored adapter via `backend/app/services/broker_factory.py` `get_broker_for_user`, used by `trading.py:_execution_for`. Secrets are encrypted at rest (`core/security.encrypt_secret`/`decrypt_secret`, Fernet keyed off `SECRET_KEY`) and only ever returned masked. |

### File map (one line each)

**Backend services** (`backend/app/services/`)
- `paper_engine.py` (423) — THE core: order placement, fills, matcher, positions, summary. Read for any trading change.
- `live_execution.py` (~230) — LIVE path: routes orders to a `BrokerAdapter`, books broker fills into the paper ledger.
- `market_data.py` (188) — quote fetching/caching via provider abstraction.
- `broker.py` (~110) — `BrokerAdapter` ABC + DTOs + `MockBrokerAdapter` (LIVE execution seam).
- `upstox_broker.py` (~150) — Upstox v2 order placement adapter (`place`/`cancel`/`status`).
- `broker_factory.py` (56) — picks mock vs upstox from `BROKER_ADAPTER`; `get_broker_for_user` resolves a user's stored Upstox connection first, falling back to server config.
- `broker_connections.py` (151) — per-user broker credential store (create/list/update/delete, encrypted at rest, masked read models, `resolve_adapter`).
- `auth.py` (137) — register/login/refresh/logout logic.
- `quote_stream.py` (136) — WebSocket quote streaming.
- `upstox.py` (113) — Upstox REST provider (live quotes).
- `provider_factory.py` (33) — picks mock vs upstox from `MARKET_DATA_PROVIDER`.
- `portfolios.py` (79), `instruments.py` (38), `users.py` (20), `audit.py` (36).

**Backend API** (`backend/app/api/v1/endpoints/`)
- `trading.py` (115) — Phase 3+4 endpoints (orders/positions/summary; dispatch by portfolio execution mode; live adapter resolved per-user).
- `portfolios.py` (61), `auth.py` (149), `market.py` (102), `instruments.py` (42), `users.py` (12), `health.py` (34), `settings.py` (38) — `GET /settings/execution` (auth) exposing non-secret execution config incl. `broker_connected`.
- `broker_connections.py` (61) — `/settings/broker` CRUD (auth, tenant-scoped).
- `router.py` (26) — registers all routers incl. broker_connections.

**Backend core** (`backend/app/core/`)
- `config.py` (94) — all env settings (incl. `PAPER_MATCHER_*`).
- `security.py` (56), `database.py` (23), `redis.py` (20), `rate_limit.py` (88).

**Backend models** (`backend/app/models/`) — `order.py` (71), `position.py` (73), `trade.py` (73), `portfolio.py` (59), `instrument.py` (58), `user.py` (53), `refresh_token.py` (42), `audit_log.py` (38), `broker_connection.py` (65). Each is a plain SQLAlchemy table.

**Backend schemas** (`backend/app/schemas/`) — thin Pydantic DTOs, 15-52 lines each.

**Backend tests** (`backend/tests/`) — read as spec: `test_paper_engine.py` (272), `test_trading_api.py` (188), `test_portfolios.py` (140), `test_market_ws.py` (90), `test_broker_connections.py` (245), others smaller. `conftest.py` (75) = fixtures; `helpers.py` (29) = `register_user`/`auth_headers`.

**Frontend** (`frontend/src/`)
- `lib/api.ts` (405) — typed API client; every backend call goes through here (incl. broker-connection CRUD).
- `lib/auth.tsx` (97), `lib/use-market-stream.ts` (203).
- `app/settings/page.tsx` (~566) — Settings page: per-portfolio paper/live switch (confirm on paper→live) + read-only Execution config card + Broker connection card (add/update token/disconnect, masked previews).
- `components/trading-panel.tsx` (517) — trade ticket + positions/orders UI.
- `components/market-quotes-card.tsx` (300), `portfolios-section.tsx` (196), `instrument-search.tsx` (131), `stat-cards.tsx` (78), `dashboard-header.tsx` (54, now has Settings link).
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

### Session 2026-08-17 — preview deploy + user feedback (no code changes)
- Deployed the preview (backend 8000 + frontend 3000 on SQLite, seeded), no
  code changes, working tree left clean. See "Running the preview" above.
- User reviewed the dashboard and requested: (1) per-portfolio strategies bar
  to add/edit strategies, (2) Settings with a live/paper mode switch and a
  place to add the broker API, (3) complained order-placing/paper-fills aren't
  discoverable and register wasn't visible. All of this is now the prioritized
  "Next step" above. Backend already supports the mode switch
  (`execution_mode` on `PATCH /portfolios/{id}`); strategies and a Settings
  page do not exist yet.

### Session 2026-08-19 — Settings page + header link (user-feedback item 2)
- New `GET /api/v1/settings/execution` (authenticated) returning non-secret
  execution config: `live_execution_enabled`, `broker_adapter` +
  `broker_is_mock`, `market_data_provider` + `market_data_is_mock`. Registered
  in `router.py`; no credentials are ever returned.
- New `frontend/src/app/settings/page.tsx`: auth-guarded Settings page with (a)
  an "Execution" card showing broker adapter / market data / live-portfolio
  availability and (b) a "Portfolio mode" list with a Paper/Live switch per
  portfolio. Switching **to live requires an inline confirmation**; switching
  back to paper is immediate (safe direction). The Live button is disabled
  with a hint when `LIVE_EXECUTION_ENABLED=false`.
- `dashboard-header.tsx` now has a Settings link (gear + label) next to Sign out.
- `api.ts` added `executionSettings()` and `updatePortfolio()` (PATCH).
- Backend tests: 3 new in `tests/test_settings.py` (auth required, defaults,
  config reflection via monkeypatch) — **109 total passing**; ruff clean;
  frontend typecheck/lint/build green (new `/settings` route generated).

### Session 2026-08-19 — per-user broker connections (user-feedback item 3)
Full-stack "add your Upstox API in Settings" — the per-user broker token store
the previous session left as the next step.

- Migration `0006` `broker_connections`: id, `user_id` (FK CASCADE, indexed),
  `provider` (default `upstox`), `label`, `access_token_encrypted`,
  `api_key_encrypted`, `is_active`, timestamps. SQLite-compatible.
- New `app/models/broker_connection.py`, `app/repositories/broker_connections.py`
  (list/get/active-for-provider/create), `app/services/broker_connections.py`
  (`BrokerConnectionService`: CRUD, max 5 connections/user, encrypted-at-rest
  secrets, masked read models), `app/schemas/broker_connection.py`
  (`BrokerConnectionCreate/Update/Read` + `mask_secret`, `****<last4>`).
- Secret storage: `app/core/security.encrypt_secret`/`decrypt_secret` — Fernet
  keyed deterministically off `SECRET_KEY` (rotation invalidates stored secrets;
  noted in `.env.example`). Never returned by the API.
- API `app/api/v1/endpoints/broker_connections.py` under `/settings/broker`
  (all auth + tenant-scoped): `GET ""` list, `POST ""` create, `PATCH /{id}`,
  `DELETE /{id}` → 204. `GET /settings/execution` now also returns
  `broker_connected` (whether the user has an active Upstox connection).
- Execution resolution: `broker_factory.get_broker_for_user(db, user_id)`
  returns a live `UpstoxBrokerAdapter` built from the user's stored credentials
  (active connection wins) falling back to the server-configured `get_broker()`.
  `trading.py:_execution_for` now uses it for live portfolios, and rejects live
  orders with a "add your Upstox API in Settings" hint when the resolved adapter
  is mock.
- Frontend: Settings page gained a "Broker connection" card — list connections
  (masked token/api preview, connected/inactive badge), add form (label, access
  token, api key), update-token inline, disconnect with confirmation; `api.ts`
  added `listBrokerConnections/createBrokerConnection/updateBrokerConnection/
  deleteBrokerConnection`; Execution card shows "Upstox (your account)" when
  `broker_connected`.
- Tests: 13 new in `tests/test_broker_connections.py` (auth required, masked
  reads, encryption round-trip + at-rest, tenant isolation, update/deactivate/
  delete, max-connections 409, short-token 422, `broker_connected` reflection,
  live order through the user's stored connection via a fake adapter,
  live order rejected without a connection) — **132 total passing**; ruff clean;
  migration `0001 → 0006` up/down/up verified; frontend typecheck/lint/build
  green.

### Session 2026-08-19 — dashboard discoverability (user-feedback item 4)
Trading was buried below the portfolios/quotes grid; the user asked that
order-placing/fills be discoverable and Register be visible.

- `/dashboard` (`frontend/src/app/dashboard/page.tsx`) now has a lightweight
  state-based **tab bar** (no new dependency): **Trading** (default, front and
  center) · **Portfolios & Quotes** · **Strategies** · **Account**. Icons from
  `lucide-react`; active tab gets a pill highlight; `aria-current` set.
- Panels are kept **mounted** and hidden with the CSS `hidden` class rather
  than unmounted, so the market WebSocket feed keeps streaming and the "Data
  mode" stat keeps updating whichever tab is active.
- Login page (`frontend/src/app/(auth)/login/page.tsx`): replaced the subtle
  "No account? Create one" text link with a divider + full-width
  **"Create a free account"** outline button linking to `/register`.
- Frontend typecheck/lint/build green (no backend change).

## Verification commands

```bash
# Backend (from backend/)
cd backend
ruff check app tests
python3 -m pytest -q          # expect 132 passed
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

## Running the preview (sandbox, no Docker/Postgres/Redis)

The preview was started on 2026-08-17 and works without Docker/Postgres/Redis.
To reproduce in a fresh session (ports: backend 8000, frontend 3000; frontend
proxies `/api/*` → backend via `next.config.mjs` rewrites):

```bash
# 1. Prep SQLite DB + seed instruments (from backend/)
cd backend
DATABASE_URL=sqlite:////tmp/tradeork.db alembic upgrade head
DATABASE_URL=sqlite:////tmp/tradeork.db python3 -m app.seed   # ~63 instruments

# 2. Backend (use background terminal, NOT a blocking shell)
cd /workspace/backend && \
DATABASE_URL=sqlite:////tmp/tradeork.db RATE_LIMIT_ENABLED=false \
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Frontend (background terminal)
cd /workspace/frontend && NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev

# 4. Request a preview URL for port 3000 (request_preview tool)
```

Notes:
- Redis is NOT required: rate limiting falls back to in-memory when Redis is
  unreachable; `/api/v1/health` reports `redis: unavailable` — harmless.
- `RATE_LIMIT_ENABLED=false` avoids 429s during interactive preview.
- `LIVE_EXECUTION_ENABLED` stays at default false unless you explicitly want
  the live-mode switch usable in the preview (it will 400 otherwise).
- The exact preview URL from the session was
  `https://3000-09d2aedd8dd31212.monkeycode-ai.live` (session-scoped; request a
  new one after the preview restarts).
- Stop servers with the background-terminal kill tool (never `pkill`).

## Next step

> **PRIORITY LIST from user feedback (2026-08-17, preview session).**
> The user previewed the app and reported it feels like "just a simple page —
> create portfolio + refresh mock data". They explicitly asked for the
> following, in their own words. **Items 2 and 3 are now DONE (2026-08-19).**
>
> 1. **A strategies bar where I can manually add or edit strategies for each
>    portfolio.** → ✅ DONE (2026-08-19): per-portfolio `strategies` model
>    (migration `0005`), CRUD API under `/portfolios/{id}/strategies`, and a
>    dashboard Strategies panel (add/edit/deactivate/delete). Strategy
>    engine/signals NOT built (roadmap Phase 7).
> 2. **In Settings: option to switch between live mode and paper trading mode.**
>    → ✅ DONE (2026-08-19): Settings page at `/settings` with a per-portfolio
>    Paper/Live switch (confirm on paper→live), wired to the existing
>    `PATCH /portfolios/{id}` `execution_mode`; Settings link in the dashboard
>    header; `GET /settings/execution` exposes live availability. Live is
>    gated server-side by `LIVE_EXECUTION_ENABLED`.
> 3. **In Settings: option to add API / the broker.** → ✅ DONE (2026-08-19):
>    per-user broker connections (`broker_connections` migration `0006`,
>    `/settings/broker` CRUD, encrypted-at-rest tokens, masked previews), a
>    "Broker connection" card on the Settings page, and live execution through
>    the user's own stored Upstox account via
>    `broker_factory.get_broker_for_user`. A real Upstox **OAuth connection
>    flow** (auth-code exchange, token refresh) is still out of scope — tokens
>    are entered manually as long-lived access tokens (see Phase 4 remaining
>    items below).
> 4. **Order placing / paper fills are not discoverable** — ✅ DONE (2026-08-19):
>    the dashboard is now a tabbed workspace with **Trading** as the default
>    front-and-center tab (Portfolios & Quotes / Strategies / Account follow);
>    the login page gained a prominent **"Create a free account"** button so
>    Register is visible.
> 5. **Remove/hide backend-health diagnostics from the user dashboard.** **NEXT.**
>    The
>    "Platform" stat (shows `Degraded` because Redis is absent in the sandbox)
>    and arguably the "Data mode" stat are dev-facing noise, not user features:
>    `dashboard/page.tsx` calls `GET /api/v1/health` and renders DB/Redis status
>    (dashboard is tabbed now but the Platform/Data-mode stats are still shown),
>    and "Data mode" renders `feedInfo` from the
>    quotes card. Recommended: drop the Platform stat entirely, or gate it (and
>    Data mode) behind `ENVIRONMENT=development` so end users only see trading
>    info. `LIVE`/`Mock` labels on the quotes card itself are fine to keep.
> 6. **Autotrade option in trading Settings.** The user wants an **"autotrade"**
>    toggle/feature alongside the paper/live switch in Settings. Define scope:
>    at minimum a per-portfolio `autotrade_enabled` flag surfaced in Settings +
>    the dashboard, ideally wired to the strategies feature (item 1) so
>    auto-generated orders run through the chosen execution mode (paper/live).
>    The paper matcher (`paper_engine.run_paper_matcher`) is the natural hook
>    for auto-placement; a manual/automated switch is needed — the user must be
>    able to turn autotrade on/off per portfolio.
>
> Suggested execution order: ~~Settings page + header link~~ (DONE) →
> ~~Strategies feature (full stack)~~ (DONE) → ~~broker token store~~ (DONE) →
> ~~dashboard discoverability/register entry point~~ (DONE) → dashboard
> diagnostic cleanup (item 5) → autotrade flag (item 6). Update this file +
> README in the same commit as always.

**Phase 4 remaining open items** (from the original roadmap, still valid but
lower priority than the user's new requests above), in suggested order:

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
6. Later phases from README: backtesting, news, AI, notifications
   (strategies + autotrade are now promoted to the user-requested list above).

If the user instead asks for a different feature, treat that as the next step
and update this file accordingly.

## Final deployment requirement (MANDATORY)

**Once the project is feature-complete, it MUST be deployed to the user's
Oracle Cloud free-tier Ubuntu server.** This is the required end state — local
sandbox and Docker Compose are only for development/verification. The full
procedure (create Ampere A1 VM, open port 80, install Docker, clone, set
`.env`, `docker compose up -d --build`, seed, update flow) is documented in
README.md under "Deploy to Oracle Cloud (final destination)". Follow that
section verbatim when the time comes.

Two deployment gotchas to keep in mind:
- `docker-compose.yml` does NOT currently pass `BROKER_ADAPTER` /
  `LIVE_EXECUTION_ENABLED` / `UPSTOX_BROKER_PRODUCT` to the backend container.
  If live execution is part of the finished product, add those env vars to the
  backend service in `docker-compose.yml` (and document them in `.env.example`).
- After deploying, verify `http://<PUBLIC_IP>/api/v1/health` reports
  `database: ok` + `redis: ok` (it shows "degraded" only in the Redis-less
  sandbox).

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
