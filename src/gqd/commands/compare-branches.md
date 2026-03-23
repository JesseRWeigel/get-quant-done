---
name: compare-branches
description: Compare results from hypothesis branches side by side
---

<process>

## Compare Branches

Compare results from two or more hypothesis branches (or main vs hypothesis).

### Step 1: Identify Branches
List available hypothesis branches:
```
git branch --list 'hypothesis/*'
```
Ask which branches to compare (default: current vs main).

### Step 2: Load Results from Each
For each branch:
- Read STATE.md for phase progress
- Read latest verification report
- Read key result files
- Note convention differences

### Step 3: Side-by-Side Comparison
Present a comparison table:

| Aspect | Branch A | Branch B |
|--------|----------|----------|
| Phases completed | 3/5 | 2/5 |
| Verification status | PASS | PARTIAL |
| Key result | ... | ... |
| Technique | ... | ... |
| Open issues | 2 minor | 1 major |

### Step 4: Recommendation
Based on the comparison, recommend:
- Merge branch X into main (if clearly better)
- Continue exploring both (if complementary)
- Abandon branch Y (if approach hit a wall)

</process>
