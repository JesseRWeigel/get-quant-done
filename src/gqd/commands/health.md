---
name: health
description: Run project health checks and optionally auto-fix issues
---

<process>

## Health Check

Run diagnostic checks on the GQD project and optionally fix issues.

### Checks

1. **Required files**: .gqd/ directory exists, STATE.md, state.json, ROADMAP.md, config.json
2. **State sync**: STATE.md and state.json are consistent (same phase, same conventions)
3. **Conventions set**: At least 3 convention locks established (warn if fewer)
4. **Uncommitted files**: Warn if more than 20 uncommitted files
5. **Git repo**: Project is in a git repository
6. **Scratch clean**: .scratch/ directory doesn't contain stale files (>7 days old)
7. **Plan consistency**: Active plans reference existing phase in ROADMAP
8. **Verification currency**: Most recent verification report is for current phase

### Output

Display a health report:
```
GQD Health Check
  ✓ Project structure
  ✓ State sync
  ⚠ Conventions: 2/10 locked (recommend locking more)
  ✓ Git: clean (3 uncommitted files)
  ✓ Plans consistent
  ✗ No verification report for current phase
```

### Auto-fix (with --fix flag)

If the user passes --fix or confirms:
- Sync STATE.md from state.json (json is authoritative)
- Remove stale .scratch/ files
- Initialize missing .gqd/ subdirectories

</process>
