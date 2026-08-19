# Tradeork — Master Product Roadmap

> **Purpose:** Long-term product and engineering source of truth. A new coding agent should read `README.md` → `HANDOVER.md` → `MASTER_ROADMAP.md` before inspecting the wider repository.
>
> **Token-saving rule:** Do NOT scan the entire repository just to rediscover project status. Use these three documents first, then inspect only files relevant to the current phase/task.
>
> **Current overall estimate:** ~70% of the intended product vision.
>
> **Current phase:** Phase 4 — Live Broker Execution.

## 1. What We Are Building

Tradeork is a multi-tenant SaaS trading platform intended to support secure accounts, Google/Gmail OAuth, user portfolios, NSE/BSE/MCX market data, paper trading, live broker trading, order/execution lifecycle management, positions, P&L, brokerage/STT/GST/exchange/SEBI/stamp-duty/slippage modelling, risk and margin management, strategies, AutoTrade, SL/target management, backtesting, notifications, reports, and production deployment on Oracle Cloud.

Target architecture:

```text
Market Data
    ↓
Strategy Engine
    ↓
Signal Engine
    ↓
Risk Engine
    ↓
Order Manager
    ↓
Broker Adapter
    ↓
Broker (e.g. Upstox)
    ↓
Execution Events / Reconciliation
    ↓
Position & Trade Ledger
    ↓
P&L / Reports / Dashboard / Notifications
```

Paper and live execution should share as much of the pipeline as practical so strategies behave consistently in backtest, paper and live modes.

## 2. Phase Status

| Phase | Area | Status |
|---|---|---|
| 1 | Foundation, Authentication & SaaS Core | ✅ Implemented foundation |
| 2 | Market Data & Portfolios | ✅ Implemented / hardening remains |
| 3 | Paper Trading | ✅ Implemented / realism expansion remains |
| 4 | Live Broker Execution | 🟡 CURRENT |
| 5 | Production Broker Infrastructure | ⬜ Next |
| 6 | Risk, Margin, SL/Target & Costs | ⬜ |
| 7 | Strategy Engine | ⬜ |
| 8 | AutoTrade | ⬜ |
| 9 | Backtesting | ⬜ |
| 10 | Notifications, Reports & SaaS Features | ⬜ |
| 11 | Oracle Cloud Production Deployment & Hardening | ⬜ |
| 12 | Final QA, Security & Launch | ⬜ |

**Overall estimate: ~68%.** This is product completeness, not code/line count.

## 3. Mandatory Agent Workflow

1. Read `README.md`.
2. Read `HANDOVER.md`.
3. Read this file.
4. Identify the current phase and next task.
5. Inspect only task-relevant files.
6. Implement the smallest coherent change.
7. Add/update tests.
8. Run relevant tests, lint, typecheck and build.
9. Run integration/E2E verification where applicable.
10. Update `HANDOVER.md` after behavior-changing work.
11. Update `README.md` when user-facing behavior changes.
12. Mark roadmap items complete only after verification.

### Definition of Done

```text
Implementation
 → Unit tests
 → Integration tests
 → E2E verification where applicable
 → Security/error-path review
 → Documentation
 → HANDOVER update
 → Verified complete
```

Never call a feature complete merely because code or a UI exists.

# Phase 1 — Foundation, Authentication & SaaS Core

**Status: ✅ Implemented foundation**

### Existing / preserve
- [x] Registration
- [x] Email/password login
- [x] Logout
- [x] JWT access tokens
- [x] Refresh-token rotation/session restoration
- [x] httpOnly refresh cookie
- [x] Argon2id password hashing
- [x] Authentication rate limiting
- [x] User/tenant ownership and isolation
- [x] Audit foundation
- [x] Portfolio CRUD
- [x] Database migrations
- [x] Docker/CI foundation

### Account requirements
- [ ] Email verification if not fully implemented
- [ ] Password reset/recovery if not fully implemented
- [ ] **Continue with Google / Gmail OAuth**
- [ ] Secure OAuth state/nonce handling
- [ ] Safely link Google login to an existing account
- [ ] Prevent duplicate accounts for the same email
- [ ] Disconnect/unlink Google account rules
- [ ] Password show/hide toggle on login
- [ ] Password show/hide toggle on registration
- [ ] Password show/hide toggle on reset/change-password
- [ ] Password strength/validation feedback
- [ ] Clear authentication errors

> Google/Gmail login means OAuth/“Continue with Google”. Tradeork must never request or store a user's Google password.

# Phase 2 — Market Data & Portfolios

**Status: ✅ Implemented / production hardening remains**

- [x] Instrument catalog/search
- [x] Market-data provider abstraction
- [x] Mock provider
- [x] Upstox REST market data
- [x] Redis caching where implemented
- [x] Authenticated market WebSocket endpoint
- [x] Frontend market-stream hook
- [x] Polling fallback
- [x] Live/mock indicator
- [ ] Production instrument-master synchronization
- [ ] Make broker WebSocket the primary live trading tick source
- [ ] WebSocket reconnect/recovery
- [ ] Stale-tick detection
- [ ] Market-data heartbeat/health metrics
- [ ] Tick latency monitoring
- [ ] Provider recovery/failover

# Phase 3 — Paper Trading

**Status: ✅ Implemented / realism expansion remains**

- [x] MARKET orders
- [x] LIMIT orders
- [x] Immediate fills
- [x] Resting-limit matcher
- [x] Cancellation
- [x] Positions and VWAP
- [x] Realized/unrealized P&L
- [x] Cash/equity summary
- [x] Trading API/UI
- [x] Background matcher
- [x] Tests/smoke flow
- [ ] Transaction-cost engine
- [ ] Slippage model
- [ ] Margin/leverage model
- [ ] Partial-fill simulation
- [ ] Spread/liquidity assumptions

# Phase 4 — Live Broker Execution

**Status: 🟡 CURRENT — partially implemented**

### Existing foundation
- [x] BrokerAdapter abstraction
- [x] Mock broker
- [x] Upstox broker adapter
- [x] Broker factory/configuration
- [x] Upstox order placement/cancel/status adapters
- [x] Portfolio `execution_mode=live`
- [x] LiveExecutionService
- [x] Live orders separated from paper orders
- [x] Broker order ID persistence
- [x] Broker fills mirrored into application ledger
- [x] Live order refresh endpoint
- [x] Paper matcher skips live orders
- [x] Live execution tests

### Finish Phase 4
- [x] User-specific broker account connections (2026-08-19)
- [x] Broker account database model (`broker_connections`, migration `0006`)
- [x] Encrypted broker token/credential storage (Fernet keyed off `SECRET_KEY`, masked reads)
- [x] User → broker account → portfolio ownership model (tenant-scoped `/settings/broker`)
- [ ] Upstox OAuth connection flow
- [ ] Automatic token lifecycle/refresh where supported
- [ ] Broker reconnect/disconnect handling
- [ ] Controlled order state machine
- [ ] Idempotent order placement
- [ ] Client order/request IDs
- [ ] Automatic order/fill synchronization
- [ ] Partial-fill handling
- [ ] Rejected/cancel-pending/unknown-state handling
- [ ] Broker reconciliation service
- [ ] Detect broker-vs-ledger discrepancies
- [ ] Independent execution worker
- [ ] Execution heartbeat and broker health
- [ ] Global trading kill switch
- [ ] Stop-new-orders control
- [ ] Cancel-all capability
- [ ] Optional emergency flatten-all capability
- [ ] Verify production Docker live-execution configuration

### Order lifecycle target

```text
CREATED → SUBMITTING → SUBMITTED → OPEN → PARTIALLY_FILLED → FILLED
                         ├→ REJECTED
                         └→ FAILED/UNKNOWN
OPEN → CANCEL_PENDING → CANCELLED
```

Exact broker mappings must be tested.

# Phase 5 — Production Broker Infrastructure

**Status: ⬜ Next**

- [ ] Broker Connections UI
- [ ] Connect Upstox account
- [ ] OAuth callback
- [ ] Secure token storage/expiry tracking
- [ ] Refresh/re-authentication
- [ ] Disconnect broker
- [ ] Connection health
- [ ] Dedicated execution worker
- [ ] Persistent order state machine
- [ ] Idempotency and safe retry policy
- [ ] Broker reconciliation loop
- [ ] Recovery after API timeout/network outage/application restart/broker outage
- [ ] Duplicate-order prevention
- [ ] Complete broker action audit trail
- [ ] Global, per-user, per-portfolio and per-strategy kill switches
- [ ] Stop-new-orders
- [ ] Cancel-open-orders
- [ ] Emergency flatten with explicit confirmation

**Exit condition:** live orders can be submitted, tracked, reconciled and recovered without manual database manipulation.

# Phase 6 — Risk, Margin, SL/Target & Costs

**Status: ⬜**

### Risk Engine
- [ ] Dedicated Risk Engine between signals and Order Manager
- [ ] Cash/margin checks
- [ ] Maximum order value
- [ ] Maximum position size
- [ ] Maximum portfolio exposure
- [ ] Maximum open positions
- [ ] Maximum daily loss
- [ ] Maximum strategy exposure
- [ ] Maximum trades/day
- [ ] Duplicate-position rules
- [ ] Trading-hours rules
- [ ] Instrument eligibility
- [ ] Kill-switch enforcement

### Margin
- [ ] Equity/cash/blocked margin/available margin
- [ ] Position exposure
- [ ] Order margin/release
- [ ] Leverage
- [ ] Intraday/overnight rules where applicable
- [ ] Broker-specific margin abstraction

### SL/Target
- [ ] Fixed-price SL
- [ ] Percentage SL
- [ ] Fixed-price target
- [ ] Percentage target
- [ ] Trailing SL
- [ ] Trailing target if supported
- [ ] Automatic exit engine
- [ ] Appropriate broker-side protection
- [ ] Paper/live consistency

### Costs/P&L
- [ ] Brokerage
- [ ] STT
- [ ] Exchange transaction charges
- [ ] SEBI charges
- [ ] GST
- [ ] Stamp duty
- [ ] Slippage
- [ ] Net P&L
- [ ] Per-order/per-trade cost breakdown
- [ ] Daily/monthly cost reporting

```text
Gross P&L
- Brokerage
- STT
- Exchange charges
- SEBI charges
- GST
- Stamp duty
- Slippage
= Net P&L
```

# Phase 7 — Strategy Engine

**Status: ⬜**

Strategies must not call brokers directly.

```text
Market Data → Strategy.evaluate() → BUY/SELL/HOLD → Risk Engine → Order Manager
```

- [ ] Common strategy interface
- [ ] Strategy registry/plugin model
- [ ] Strategy lifecycle/versioning
- [ ] Parameter validation
- [ ] Strategy CRUD
- [ ] Create/edit/clone/archive/delete
- [ ] Activate/deactivate
- [ ] Instruments/timeframe configuration
- [ ] Entry/exit rules
- [ ] SL/target/trailing configuration
- [ ] Capital allocation
- [ ] Maximum trades
- [ ] Trading sessions
- [ ] Strategy logs
- [ ] RSI strategy
- [ ] EMA crossover
- [ ] VWAP
- [ ] Supertrend
- [ ] Breakout
- [ ] Custom strategy framework

# Phase 8 — AutoTrade

**Status: ⬜**

Required pipeline:

```text
Live Market Data
 → Strategy Engine
 → Signal Engine
 → Signal validation/deduplication
 → Risk Engine
 → Order Manager
 → Broker Adapter
 → Upstox
 → Execution Events
 → Position Ledger
```

- [ ] AutoTrade enable/disable per portfolio
- [ ] AutoTrade enable/disable per strategy
- [ ] Maximum trades/day
- [ ] Maximum daily loss
- [ ] Maximum open positions
- [ ] Maximum capital allocation
- [ ] Maximum symbol exposure
- [ ] Cooldown
- [ ] Trading hours
- [ ] Duplicate signal protection
- [ ] Signal IDs
- [ ] Execution status
- [ ] Automatic entry
- [ ] Automatic SL
- [ ] Automatic target
- [ ] Automatic trailing SL
- [ ] Automatic exit
- [ ] Position reconciliation
- [ ] Failed-order handling
- [ ] Broker disconnect handling
- [ ] Restart recovery
- [ ] Emergency stop

**Safety rule:** AutoTrade must never bypass the Risk Engine.

# Phase 9 — Backtesting

**Status: ⬜**

Same strategy interface should work across historical, paper and live execution where practical.

- [ ] Historical data provider
- [ ] Timeframes
- [ ] Strategy execution
- [ ] Entry/exit simulation
- [ ] SL/target/trailing simulation
- [ ] Partial-fill assumptions
- [ ] Slippage
- [ ] Brokerage/STT/taxes/charges
- [ ] Position sizing
- [ ] Margin simulation
- [ ] Net/gross P&L
- [ ] Win/loss rate
- [ ] Profit factor
- [ ] Maximum drawdown
- [ ] Sharpe ratio
- [ ] Average win/loss
- [ ] Number of trades
- [ ] Equity curve
- [ ] Daily/monthly performance
- [ ] Trade-by-trade report
- [ ] Avoid look-ahead bias
- [ ] Document assumptions
- [ ] Compare backtest vs paper

# Phase 10 — Notifications, Reports & SaaS Features

**Status: ⬜**

### Notifications priority
1. [ ] Telegram
2. [ ] Email
3. [ ] WhatsApp

Events:
- [ ] Order submitted/filled/rejected/cancelled
- [ ] SL/target/trailing SL
- [ ] AutoTrade started/stopped
- [ ] Daily loss limit
- [ ] Broker disconnect
- [ ] Market feed disconnect
- [ ] Strategy error
- [ ] System health warning

### Reports
- [ ] Daily/weekly/monthly reports
- [ ] Trade history
- [ ] P&L report
- [ ] Charges report
- [ ] Strategy performance
- [ ] Broker execution report
- [ ] CSV/PDF export where appropriate

### SaaS/account
- [x] Trading settings (per-portfolio paper/live switch) — Settings page at `/settings` (2026-08-19); live gated by `LIVE_EXECUTION_ENABLED`
- [x] Read-only execution config (broker adapter / market-data provider / live availability via `GET /settings/execution`)
- [x] Broker settings — per-user broker connection CRUD (`/settings/broker`, migration `0006`, encrypted-at-rest tokens, Settings UI card; 2026-08-19). OAuth connect flow and token refresh pending (Phase 4).
- [ ] Account settings
- [ ] Risk settings
- [ ] Notification settings
- [ ] Session/device management
- [ ] Account deletion
- [ ] Data export
- [ ] Subscription/billing architecture if monetized

# Phase 11 — Oracle Cloud Production Deployment & Hardening

**Status: ⬜**

Target deployment: Oracle Cloud as specified by project documentation.

### Deployment
- [ ] Production Docker configuration
- [ ] PostgreSQL
- [ ] Redis
- [ ] API
- [ ] Frontend
- [ ] Market-data worker
- [ ] Trading/execution worker
- [ ] Background jobs
- [ ] Reverse proxy
- [ ] HTTPS/TLS
- [ ] Domain
- [ ] Secret/environment management
- [ ] Live broker configuration verified

### Reliability
- [ ] Health checks
- [ ] Automatic service restart
- [ ] Worker heartbeat
- [ ] Database backups
- [ ] Restore test
- [ ] Redis recovery
- [ ] Broker recovery
- [ ] WebSocket recovery
- [ ] Server restart recovery
- [ ] Clock/timezone consistency

### Observability
- [ ] Structured logging
- [ ] Error tracking
- [ ] API/database/Redis/broker/market-data health
- [ ] Execution latency
- [ ] Failed-order metrics
- [ ] Worker heartbeat
- [ ] Critical-failure alerts

### Security
- [ ] HTTPS
- [ ] Secret rotation plan
- [ ] Least-privilege DB access
- [ ] Secure CORS
- [ ] Rate limiting
- [ ] Security headers
- [ ] Input validation
- [ ] Audit logs
- [ ] No secrets in repository
- [ ] Dependency/security scanning
- [ ] Production DEBUG disabled

# Phase 12 — Final QA, Security & Launch

**Status: ⬜**

### Functional QA
- [ ] Registration
- [ ] Email/password login
- [ ] Google login
- [ ] Password show/hide
- [ ] Password reset
- [ ] Portfolio creation
- [ ] Instrument search
- [ ] Live market data
- [ ] Paper trading
- [ ] Live broker connection
- [ ] Live order/cancel/fill/rejection/partial fill
- [ ] Reconciliation
- [ ] SL/target
- [ ] AutoTrade
- [ ] Strategy management
- [ ] Backtest
- [ ] Notifications
- [ ] Reports

### Failure testing
- [ ] Broker timeout/disconnect
- [ ] WebSocket disconnect
- [ ] Redis/database outage
- [ ] Restart during order submission
- [ ] Restart after fill
- [ ] Duplicate request/signal
- [ ] Token expiry
- [ ] Invalid broker credentials
- [ ] Network outage
- [ ] Partial fill/rejection
- [ ] Stale market data

### Security QA
- [ ] Tenant isolation
- [ ] Authorization
- [ ] OAuth security
- [ ] Token protection
- [ ] Injection checks
- [ ] Rate limits
- [ ] Secret scanning
- [ ] Dependency vulnerability scan
- [ ] Audit-log verification

**100% / production-ready means implemented + tested + integrated + documented + verified.**

# 4. Current Execution Order

Do not jump randomly between features.

```text
Phase 1 Foundation/Auth              ✅
        ↓
Phase 2 Market Data/Portfolios       ✅
        ↓
Phase 3 Paper Trading                ✅
        ↓
Phase 4 Live Broker Execution        🟡 CURRENT
        ↓
Phase 5 Production Broker Infra      ⬜ NEXT
        ↓
Phase 6 Risk/Margin/SL/Costs         ⬜
        ↓
Phase 7 Strategy Engine              ⬜
        ↓
Phase 8 AutoTrade                    ⬜
        ↓
Phase 9 Backtesting                  ⬜
        ↓
Phase 10 Notifications/SaaS          ⬜
        ↓
Phase 11 Oracle Production           ⬜
        ↓
Phase 12 QA/Security/Launch          ⬜
```

Before real-money AutoTrade, the minimum dependable chain is:

```text
Broker connection
 → Token lifecycle
 → Order state machine
 → Idempotency
 → Broker reconciliation
 → Execution worker
 → Risk engine
 → Margin
 → SL/Target
 → Transaction costs
 → Kill switch
 → Strategy engine
 → AutoTrade
```

# 5. Architectural Rules

1. Do not rewrite working architecture without a demonstrated reason.
2. Preserve tenant isolation.
3. Preserve paper/live execution separation.
4. Strategies must not call brokers directly.
5. Strategy generates signals; Risk Engine decides whether orders are allowed; Order Manager executes them.
6. AutoTrade must never bypass risk controls.
7. Never store broker secrets or Google passwords in plaintext.
8. Never store a user's Google/Gmail password.
9. Use idempotency for externally executed orders.
10. Broker reconciliation is mandatory for live trading.
11. A successful API response is not proof of complete live execution.
12. Prefer broker WebSocket for real-time trading data; REST is for snapshots/recovery/historical data.
13. Keep paper/backtest/live strategy interfaces as consistent as practical.
14. Add tests for behavior-changing features.
15. Update `HANDOVER.md` after behavior-changing work.
16. Update `README.md` when user-facing behavior changes.
17. Update this roadmap if phase scope/architecture changes.
18. Avoid unnecessary repository-wide reading.
19. Avoid large features mixed with unrelated refactors.
20. Never claim a phase complete until exit conditions are verified.

# 6. Token-Efficient Agent Reading Plan

A fresh agent should normally need only:

```text
README.md
   ↓
HANDOVER.md
   ↓
MASTER_ROADMAP.md
   ↓
Only task-relevant files named/discovered for the current phase
```

Examples:

- Broker task → inspect broker adapter, live execution service, order models/routes, migrations, settings and tests.
- Strategy task → inspect strategy modules, market-data interfaces, risk/order interfaces and tests.
- Auth task → inspect auth routes/services/models, frontend auth pages/components, OAuth configuration and tests.

Do not read all 8,000–10,000 lines unless the task genuinely requires repository-wide analysis.

# 7. Final Product Workflow

```text
User
 ↓
Secure Account / Google OAuth
 ↓
Portfolio
 ↓
Broker Connection
 ↓
Live Market Data
 ↓
Strategy
 ↓
Signal
 ↓
Risk / Margin / Limits
 ↓
Order Manager
 ↓
Broker Adapter
 ↓
Broker
 ↓
Execution / Reconciliation
 ↓
Positions / Trades
 ↓
SL / Target / Auto Exit
 ↓
Charges / Slippage
 ↓
Accurate Net P&L
 ↓
Reports / Dashboard / Notifications
```

The same strategy should be usable, with appropriate execution adapters, in:

```text
Backtest → Paper → Live
```

**This is the target Tradeork architecture.**
