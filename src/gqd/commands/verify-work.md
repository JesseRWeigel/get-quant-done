---
name: verify-work
description: Run the 12-check financial verification framework
---

<process>

## Verify Work

### Overview
Run post-hoc verification on completed phase work using the 12-check framework.

### Step 1: Collect Artifacts
Gather all output from the current phase:
- Derivation files (LaTeX/markdown)
- Implementation scripts (Python)
- Backtest results (CSV/JSON)
- SUMMARY files from executors

### Step 2: Build Evidence Registry
Extract verification evidence from artifacts:
- No-arbitrage conditions checked
- Option pricing consistency (put-call parity)
- Greeks computed and compared
- Boundary conditions tested
- Distribution assumptions and tests
- Backtest methodology details
- Statistical test results
- Risk measure properties
- P&L attribution

### Step 3: Run Verification
Spawn gqd-verifier with:
- All phase artifacts
- Evidence registry
- Convention locks
- LLM error catalog

### Step 4: Process Verdict
Parse the VERIFICATION-REPORT.md:
- If PASS: record in state, proceed
- If PARTIAL: create targeted gap-closure for MAJOR failures
- If FAIL: create gap-closure for CRITICAL failures, block downstream

### Step 5: Route Failures
For each failure, route to the appropriate agent:
- No-arbitrage violations — gqd-executor (targeted re-derivation)
- Backtest integrity issues — gqd-backtester (bias fix)
- Statistical issues — gqd-executor (reanalysis with corrections)
- Convention drift — convention resolution
- Robustness failures — gqd-backtester (additional sensitivity tests)

### Step 6: Update State
Record verification results in STATE.md:
- Verdict hash (content-addressed)
- Pass/fail counts
- Any unresolved issues

</process>
