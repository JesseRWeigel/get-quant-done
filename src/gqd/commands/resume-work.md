---
name: resume-work
description: Resume work after a session interruption
---

<process>

## Resume Work

### Overview
Restore context and resume from where the last session left off.

### Step 1: Load State
Read STATE.md and state.json via gqd-state.

### Step 2: Check for Crash Recovery
Run state engine recovery:
- If intent marker exists, reconcile state
- Sync STATE.md with state.json

### Step 3: Check for Continue-Here
If `.gqd/.continue-here.md` exists:
- Read it for exact position, intermediate results, and planned next steps
- This is the highest-priority resume path

### Step 4: Check for Partial Completion
If no continue-here file:
- Scan git log for recent [gqd] commits
- Identify last completed task
- Determine which plan/wave was in progress

### Step 5: Present Resume Options
Show the user:
- Current phase and plan
- Last completed task
- What remains to be done
- Any unresolved verification issues

Offer options:
1. **Resume from checkpoint** — continue from where we left off
2. **Re-execute current plan** — start the current plan from scratch
3. **Skip to next plan** — mark current plan as complete (with warning)
4. **Run verification** — verify what's been completed so far

### Step 6: Resume
Based on user choice (or auto-choice in yolo mode):
- Restore convention locks
- Resume the appropriate command (execute-phase, plan-phase, etc.)

</process>
