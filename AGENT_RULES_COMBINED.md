# Tradeork — AGENT_RULES.md

> **Purpose:** Authoritative operating rules for AI coding agents working on Tradeork.
>
> **Primary goal:** Build Tradeork correctly and safely while minimizing unnecessary repository reading, repeated code generation, rewrites, debugging loops, token consumption, and scope creep.

---

# 1. Authority and Context Chain

`AGENT_RULES.md` is the authoritative operating document for Tradeork AI coding agents.

Every new AI coding session should follow:

```text
README.md
    ↓
HANDOVER.md
    ↓
MASTER_ROADMAP.md
    ↓
AGENT_RULES.md
    ↓
Current phase
    ↓
One current task
    ↓
Relevant files only
    ↓
Minimum patch
    ↓
Targeted tests
    ↓
Verification
    ↓
HANDOVER update
    ↓
Commit + push when the unit is green
    ↓
STOP
```

Required reading order:

1. `README.md`
2. `HANDOVER.md`
3. `MASTER_ROADMAP.md`
4. `AGENT_RULES.md`
5. Only task-relevant code

Do **not** scan the entire repository.

Before coding, determine:

- What Tradeork is
- Current architecture
- Completed phases
- Current active phase
- Current roadmap task
- Existing functionality
- Known limitations
- What must not be rebuilt

---

# 2. Core Engineering Principle

Do not behave like a code generator that repeatedly rewrites code until something appears to work.

Use:

```text
Understand
    ↓
Search
    ↓
Bounded / targeted inspection
    ↓
Identify root cause
    ↓
Make the smallest correct change
    ↓
Test
    ↓
Verify
    ↓
Update documentation if required
    ↓
Commit + push when the unit is green
    ↓
STOP
```

Priorities:

1. Correctness
2. Trading safety
3. Security
4. Minimal code changes
5. Token efficiency
6. Testing
7. Speed

---

# 3. One Task at a Time

A coding session should have **one coherent task**.

At startup, state:

```text
CURRENT PHASE:
<phase>

CURRENT TASK:
<one task>

EXISTING IMPLEMENTATION:
<what already exists>

DEPENDENCIES:
<only required dependencies>

EXPECTED FILES:
<files likely to change>

PLAN:
1. <step>
2. <step>
3. <step>
```

Do not mix the requested task with unrelated:

- Refactoring
- Formatting
- Dependency upgrades
- Architectural rewrites
- UI redesigns
- Naming changes
- Cleanup
- Speculative improvements

If unrelated improvements are discovered, leave them for a separate task.

---

# 4. Follow the Master Roadmap

The roadmap is the execution plan.

Current intended sequence:

```text
Phase 1 — Foundation/Auth
        ↓
Phase 2 — Market Data/Portfolios
        ↓
Phase 3 — Paper Trading
        ↓
Phase 4 — Live Broker Execution
        ↓
Phase 5 — Production Broker Infrastructure
        ↓
Phase 6 — Risk/Margin/SL/Costs
        ↓
Phase 7 — Strategy Engine
        ↓
Phase 8 — AutoTrade
        ↓
Phase 9 — Backtesting
        ↓
Phase 10 — Notifications/Reports/SaaS
        ↓
Phase 11 — Production Deployment/Hardening
        ↓
Phase 12 — Final QA/Security/Launch
```

Work on the current phase unless a dependency requires otherwise.

Do not implement future features merely because they appear on the roadmap.

Do not mark roadmap items complete merely because code exists.

A feature is complete only when it is:

```text
Implemented
+
Tested
+
Integrated
+
Verified
+
Documented
```

---

# 5. Search Before Creating Anything

Before creating a:

- Service
- Route
- Controller
- Component
- Hook
- Utility
- Model
- Migration
- Table
- Broker adapter
- Execution service
- Strategy interface
- Background worker

search the repository first.

Ask:

> Does this already exist?

If yes:

- Reuse it
- Extend it
- Fix it
- Refactor only when necessary

Do not create a second implementation of the same concept.

---

# 6. Token-Efficient Repository Exploration

Use:

```text
SEARCH
  ↓
BOUNDED INSPECTION
  ↓
PATCH
  ↓
TARGETED TEST
```

Not:

```text
OPEN EVERYTHING
  ↓
READ EVERYTHING
  ↓
REWRITE EVERYTHING
```

When looking for a function/class/route/model/component:

1. Search for its name.
2. Find its definition.
3. Find its callers.
4. Find relevant tests.
5. Inspect only the necessary sections.

Prefer bounded reads and targeted searches.

Do not:

- Read thousands of lines without a reason
- Dump entire large files into context
- Reopen unchanged files
- Reprint unchanged code
- Repeat the same repository search unnecessarily

Before every major action ask:

> Does this materially help solve the current task?

If not, do not do it.

---

# 7. Minimum Patch Principle

Always make the smallest change capable of solving the problem.

If one line fixes it:

```text
CHANGE ONE LINE.
```

If five lines fix it:

```text
CHANGE FIVE LINES.
```

Do not rewrite a 300-line function because one condition is wrong.

Do not regenerate an entire file when only a small section needs modification.

This reduces:

- Token usage
- Accidental regressions
- Merge conflicts
- Review difficulty

---

# 8. Never Rewrite Working Code Without a Reason

Working code is an asset.

Do not replace working code merely because:

- You prefer another architecture
- You prefer another naming convention
- Another framework looks cleaner
- You can make the code shorter
- You would have designed it differently
- A different implementation is fashionable

Only change existing working code when there is a concrete requirement, bug, security issue, or verified technical need.

---

# 9. Never Duplicate Existing Logic

Avoid duplicate implementations of:

- Authentication
- Authorization
- Tenant isolation
- Broker communication
- Order handling
- Risk checks
- P&L calculations
- Market-data handling
- Strategy execution
- Notification handling

Prefer one authoritative implementation.

If existing code is 80–90% suitable, modify it rather than creating a replacement.

---

# 10. Debugging Protocol

When something fails, do **not** immediately rewrite the implementation.

Follow:

### Step 1
Read the exact error.

### Step 2
Locate the exact file/function/line involved.

### Step 3
Inspect surrounding code.

### Step 4
Identify the root cause.

### Step 5
Make the smallest possible fix.

### Step 6
Run the smallest relevant test.

### Step 7
Verify the result.

### Step 8
If fixed, stop.

When a failure depends on:

- Runtime configuration
- Environment variables
- Broker behavior
- API response format
- Database state
- Authentication state
- WebSocket state
- External service behavior

inspect the actual evidence.

Do not repeatedly change application code based on guesses.

---

# 11. Repeated Failure Emergency Rule

If the same error remains after a fix:

**Do not rewrite the same code again.**

If the same failure happens twice:

```text
STOP MODIFYING CODE.
```

Investigate:

- Actual runtime error
- Logs
- Configuration
- Environment
- Database state
- API response
- Network behavior
- Dependency version
- Test assumptions
- State transitions

Then make **one evidence-based change**.

Use:

```text
Attempt
    ↓
Failure
    ↓
Investigate
    ↓
Understand
    ↓
Targeted correction
    ↓
Test
    ↓
Verify
```

Never use:

```text
Rewrite
    ↓
Fail
    ↓
Rewrite again
    ↓
Fail
    ↓
Rewrite again
```

When appropriate explicitly state:

> **REPEATED FAILURE — stopping implementation to investigate root cause.**

---

# 12. Testing Discipline

Test the smallest relevant surface first.

Preferred progression:

```text
Targeted unit test
        ↓
Targeted integration test
        ↓
Broader tests
        ↓
Full suite before phase completion
```

Do not run the entire repository test suite after every tiny change unless required.

For example, changing order cancellation should begin with:

```text
Cancellation unit test
    ↓
Broker integration test
    ↓
Execution tests
    ↓
Full suite when appropriate
```

Do not repeatedly run identical checks without a change that could affect the result.

Once the current unit of work is green and verified, stop testing that unit unless broader validation is required.

---

# 13. Commit and Push Discipline

When the current coherent unit of work is:

- implemented,
- tested,
- verified,
- and green,

commit it promptly.

Do not accumulate unrelated changes into one commit.

Use:

```text
ONE COHERENT TASK
    ↓
TEST
    ↓
VERIFY
    ↓
COMMIT
    ↓
PUSH
    ↓
STOP
```

Do not commit:

- Secrets
- Tokens
- Temporary debugging output
- Generated junk
- Unrelated modifications

Before committing, inspect the changed files and ensure the diff contains only the intended task.

---

# 14. Dependencies

Before installing a dependency:

1. Search existing dependencies.
2. Check whether an existing library already solves the problem.
3. Add a dependency only when there is a clear benefit.

Avoid dependency bloat.

Do not upgrade dependencies as part of an unrelated task.

---

# 15. Database Discipline

Before creating a migration:

- Search existing migrations.
- Inspect models.
- Check whether the table already exists.
- Check whether the column already exists.
- Check existing indexes/constraints.

Never create duplicate database structures.

Never perform destructive production database changes without explicit authorization.

Prefer backward-compatible migrations.

---

# 16. Trading-System Safety

Tradeork is a trading system, not a normal CRUD application.

Extra caution is required for:

- Live orders
- Broker adapters
- Order state
- Fills
- Positions
- Reconciliation
- Risk
- Margin
- SL/target
- AutoTrade
- P&L
- Transaction costs

The intended execution pipeline is:

```text
Market Data
    ↓
Strategy
    ↓
Signal
    ↓
Risk Engine
    ↓
Order Manager
    ↓
Broker Adapter
    ↓
Broker
    ↓
Execution Event
    ↓
Position/Trade Ledger
    ↓
Reconciliation
```

Critical rules:

- Strategies must **not** directly call brokers.
- AutoTrade must **not** bypass the Risk Engine.
- Never assume API success means the trade definitely completed.

A broker order can be:

- Accepted
- Rejected
- Partially filled
- Delayed
- Cancelled
- Left in an unknown state

The system must handle those states explicitly.

---

# 17. Paper and Live Trading Must Remain Separate

Never accidentally mix paper and live execution.

Preserve explicit execution modes.

A paper-trading change must not silently modify live trading.

A live-execution change must not silently break paper trading.

If shared code changes affect both modes, test both modes.

---

# 18. Live Order Idempotency

Any live order implementation must account for:

- Duplicate requests
- Retries
- Network timeout
- Broker timeout
- Application restart
- Unknown broker state
- Partial fills

Never respond to a broker timeout by blindly sending another order.

First determine whether the original order exists.

Use where appropriate:

- Idempotency keys
- Client order IDs
- Broker order IDs
- Persistent order state
- Reconciliation

---

# 19. Broker Reconciliation Is Mandatory

Live execution must eventually reconcile:

```text
Tradeork Ledger
      ↕
Broker State
```

The system must be able to detect:

- Missing orders
- Duplicate orders
- Unexpected fills
- Partial fills
- Rejected orders
- Cancelled orders
- Position differences
- Stale state

Do not mark live execution production-ready without reconciliation.

---

# 20. Risk Engine Rules

The intended order path is:

```text
Signal
   ↓
Risk Engine
   ↓
Order Manager
   ↓
Broker
```

The Risk Engine should eventually enforce things such as:

- Available cash/margin
- Maximum order value
- Maximum position size
- Maximum exposure
- Maximum open positions
- Maximum daily loss
- Maximum trades/day
- Strategy limits
- Trading hours
- Instrument eligibility
- Kill switches

Never implement AutoTrade in a way that bypasses these controls.

---

# 21. Authentication and Account Security

For Google/Gmail login:

- Use Google OAuth.
- Never request a user's Google password.
- Never store a Google password.
- Protect OAuth state/nonce.
- Safely link Google identity to an existing account.
- Prevent duplicate account creation.
- Securely handle disconnect/unlink.

For manual password login:

- Preserve secure password hashing.
- Preserve rate limiting.
- Provide password show/hide UI where specified.
- Never log passwords.
- Never expose passwords through API responses.

---

# 22. Live Broker Credentials

Never:

- Hard-code broker secrets.
- Commit tokens.
- Print tokens in logs.
- Expose secrets in frontend code.
- Store secrets in plaintext unnecessarily.

Use secure server-side storage and appropriate environment/secret management.

---

# 23. Configuration Discipline

Before changing:

- Environment variables
- Docker configuration
- Database configuration
- Broker configuration
- OAuth configuration
- Reverse proxy configuration
- Deployment configuration

inspect the existing configuration and understand its role.

Do not replace configuration wholesale.

Patch only what is required.

---

# 24. Feature Already Implemented

If the requested feature already exists:

Do not rebuild it.

Verify:

- Implementation
- Tests
- Integration
- Edge cases

Then report:

> **ALREADY IMPLEMENTED — NO CODE CHANGE REQUIRED.**

Only modify it if a real missing requirement or bug is identified.

---

# 25. Phase Discipline

At the beginning:

```text
CURRENT PHASE:
CURRENT TASK:
DEPENDENCIES:
EXPECTED FILES TO CHANGE:
```

At completion:

```text
COMPLETED:
FILES CHANGED:
TESTS:
RESULT:
NEXT ROADMAP ITEM:
```

Do not mark unfinished work complete.

---

# 26. Handover Discipline

After meaningful behavior-changing work, update `HANDOVER.md` with only the necessary changes:

- Completed work
- Current state
- Known issues
- Next recommended task

Do not rewrite the entire handover.

Update `README.md` when user-facing behavior changes.

Update `MASTER_ROADMAP.md` when:

- Phase status changes
- Scope changes
- Architecture changes
- A roadmap item is genuinely completed

---

# 27. Stop Conditions

Stop coding when:

- Requested functionality works
- Relevant tests pass
- Verification succeeds
- No additional code is required

Do not continue indefinitely "improving" a completed task.

If complete:

**STOP.**

Do not invent additional work.

---

# 28. Ambiguous Requirements

If ambiguity affects only minor implementation details:

- Inspect the existing architecture.
- Choose the smallest safe implementation.

If ambiguity affects:

- Money
- Live trading
- Security
- Database integrity
- Broker execution
- Risk controls

do not make a large assumption.

Ask for clarification or clearly document the blocking assumption.

---

# 29. No Speculative Overengineering

Do not build infrastructure "just in case."

Do not add:

- Unused abstractions
- Unused services
- Unused endpoints
- Unused database tables
- Unused configuration
- Speculative microservices
- Unnecessary queues
- Unnecessary dependencies

Build what the current roadmap task requires.

Design for future extension where practical, but do not implement the future prematurely.

---

# 30. Preserve Existing Architecture

Do not rewrite the architecture simply because another architecture is possible.

Before proposing an architectural change, establish:

1. What problem exists?
2. Why the current architecture cannot solve it?
3. What is the smallest architectural change?
4. What existing functionality could break?
5. What tests prove the change is safe?

Architecture changes require justification.

---

# 31. Final Completion Report

After implementation, report:

```text
TASK:
<one sentence>

CURRENT PHASE:
<phase>

CHANGES:
- <file>: <short description>
- <file>: <short description>

TESTS:
- <test>
- <test>

RESULT:
PASS / PARTIAL / BLOCKED

NEXT:
<single next roadmap task>

TOKEN DISCIPLINE:
No unnecessary rewrites / targeted patch / minimal files changed

COMMIT:
<commit hash/message if committed>

PUSH:
<yes/no>
```

Keep the report concise.

---

# 32. Final Engineering Rules

The following rules override convenience:

1. **Do not write code that already exists.**
2. **Do not rewrite code that already works.**
3. **Do not inspect code irrelevant to the current task.**
4. **Use bounded, targeted repository reads.**
5. **Do not repeatedly attempt the same fix.**
6. **Do not guess when runtime evidence is available.**
7. **Do not bypass the roadmap.**
8. **Do not bypass the Risk Engine for AutoTrade.**
9. **Do not blindly retry live broker orders.**
10. **Do not mix paper and live execution.**
11. **Do not expose secrets.**
12. **Do not create unnecessary dependencies.**
13. **Do not expand task scope without a reason.**
14. **Do not mark unfinished work complete.**
15. **Test every meaningful behavior change.**
16. **Update HANDOVER after meaningful changes.**
17. **Commit only coherent, verified work.**
18. **Push only the intended changes.**
19. **Prefer a one-line fix over a 100-line rewrite.**
20. **Stop when the task is complete.**

---

# 33. The Golden Rule

> ## DO NOT WRITE MORE CODE.
> ## WRITE THE MINIMUM CORRECT CODE.
>
> ## DO NOT READ MORE FILES.
> ## READ ONLY WHAT IS NECESSARY.
>
> ## DO NOT REPEAT IMPLEMENTATIONS.
> ## REUSE EXISTING CODE.
>
> ## DO NOT REWRITE WORKING CODE.
> ## PATCH THE ROOT CAUSE.
>
> ## DO NOT GUESS.
> ## USE RUNTIME EVIDENCE.
>
> ## TEST THE CHANGE.
> ## COMMIT THE VERIFIED UNIT.
> ## STOP WHEN DONE.

Tradeork must evolve through **small, evidence-based, verified, incremental changes**, not repeated large rewrites.
