---
name: execute-phase
description: Execute the current phase — the main research loop
---

<process>

## Execute Phase

Read `{GQD_INSTALL_DIR}/specs/workflows/execute-phase-workflow.md` first. Do NOT improvise.

### Overview
This is the main execution loop. It:
1. Loads ROADMAP.md and STATE.md
2. Discovers all PLAN.md files for the current phase
3. Computes dependency-ordered waves
4. Executes tasks in parallel within each wave via subagent delegation
5. Verifies artifacts after each wave
6. Runs post-phase verification
7. Handles gap closure if verification fails

### Pre-execution
1. Load state via gqd-state
2. Check conventions via gqd-conventions
3. Verify plans exist for current phase
4. Create rollback checkpoint tag

### Wave Execution Loop
For each wave (in order):
1. Log wave start
2. For each plan/task in the wave (parallel):
   a. Spawn gqd-executor subagent with task context
   b. Collect return envelope
   c. Verify artifacts on disk (artifact recovery protocol)
   d. Commit task artifacts
3. Log wave completion
4. Run inter-wave verification if configured (convention/consistency checks)
5. Update STATE.md

### Post-Phase Verification
After all waves complete:
1. Spawn gqd-verifier with all phase artifacts
2. Parse verification verdict
3. If PASS: mark phase complete, advance to next phase
4. If FAIL: create gap-closure plans for failed checks
5. Re-execute gap-closure plans with --gaps-only flag
6. Maximum 2 gap-closure iterations, then flag UNRESOLVED

### Error Handling
- Subagent failure: analyze, create targeted re-execution plan
- Convention violation: route to convention resolution
- Context pressure: checkpoint and resume in fresh session

</process>
