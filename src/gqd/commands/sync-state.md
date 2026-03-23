---
name: sync-state
description: Reconcile STATE.md and state.json after manual edits
---

<process>

## Sync State

Reconcile STATE.md and state.json when they've diverged (e.g., after manual edits).

### Process
1. Load state.json (authoritative source)
2. Re-render STATE.md from state.json
3. Report what changed
4. Commit the sync if there were changes

If state.json is missing but STATE.md exists, offer to reconstruct state.json from STATE.md.

</process>
