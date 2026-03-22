# Agent Delegation Protocol

> How the orchestrator spawns subagents, collects results, and handles failures.

## Task Delegation Pattern

```
orchestrator
  ├── spawn(gqd-researcher, {phase_goal})  → RESEARCH.md
  ├── spawn(gqd-planner, {research, phase_goal})  → PLAN.md
  ├── validate(plan)  → APPROVE / REVISE / REJECT
  │   └── if REVISE: loop back to planner (max 3 iterations)
  ├── for each wave:
  │   ├── spawn(gqd-executor, {task_1})  → artifacts + SUMMARY
  │   ├── spawn(gqd-executor, {task_2})  → artifacts + SUMMARY  (parallel)
  │   ├── spawn(gqd-backtester, {task_3})  → backtest + SUMMARY  (if applicable)
  │   └── verify_artifacts_on_disk()
  ├── spawn(gqd-verifier, {phase_artifacts})  → VERIFICATION-REPORT.md
  │   └── if FAIL: create gap-closure plans, re-execute
  └── update STATE.md
```

## Artifact Recovery Protocol

**CRITICAL**: Never trust that a subagent's reported success means files were written.

After every subagent returns:
1. Parse the `gqd_return` envelope from SUMMARY.md
2. Verify every file in `files_written` exists on disk
3. If missing: attempt to extract content from the agent's response text
4. If still missing: log error and flag for re-execution

## Return Envelope Parsing

Every subagent MUST produce a `gqd_return:` YAML block in their SUMMARY.md:

```yaml
gqd_return:
  status: completed | checkpoint | blocked | failed
  files_written: [...]
  files_modified: [...]
  issues: [...]
  next_actions: [...]
  claims_validated: [...]
  conventions_proposed: {field: value}
  verification_evidence: {...}
```

The orchestrator uses this structured data — NOT the agent's prose — to determine:
- Whether to proceed to the next wave
- What files to verify
- What convention proposals to evaluate
- What verification evidence to feed to the verifier

## Failure Handling

| Agent Status | Orchestrator Action |
|-------------|-------------------|
| `completed` | Verify artifacts, proceed |
| `checkpoint` | Save state, can resume later |
| `blocked` | Analyze blocker, may route to different agent |
| `failed` | Analyze failure, create targeted re-execution plan |

## Context Budget

Each subagent gets a fresh context window. The orchestrator targets ~15% of its own context for coordination. Budget allocation per phase type:

| Phase Type | Orchestrator | Planner | Executor | Verifier | Backtester |
|-----------|-------------|---------|----------|----------|------------|
| Literature survey | 10% | 5% | 70% | 15% | 0% |
| Model derivation | 15% | 10% | 50% | 25% | 0% |
| Implementation | 10% | 5% | 60% | 25% | 0% |
| Backtesting | 10% | 5% | 20% | 25% | 40% |
| Paper writing | 10% | 5% | 70% | 15% | 0% |
