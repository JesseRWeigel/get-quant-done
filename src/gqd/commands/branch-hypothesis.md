---
name: branch-hypothesis
description: Create a parallel investigation branch for an alternative approach
---

<process>

## Branch Hypothesis

Create a git branch to explore an alternative approach or strategy
without contaminating the main research line.

### Step 1: Name the Branch
Ask the user for:
- Branch name (e.g., "alternative-method", "new-framework")
- Description of the alternative approach
- What phase/task this branches from

### Step 2: Create Branch
```
git checkout -b hypothesis/{branch-name}
```

Copy current state files so the branch has full context.

### Step 3: Document the Hypothesis
Create .gqd/HYPOTHESIS.md with:
- Branch name and creation date
- Parent branch/commit
- Alternative approach description
- Success criteria (what would make this approach worth merging?)
- Estimated effort

### Step 4: Work on the Branch
The user can now run normal GQD commands (plan-phase, execute-phase, etc.)
on this branch. All work is isolated from main.

### Step 5: Compare (via /gqd:compare-branches)
When ready, use compare-branches to compare results side by side.

</process>
