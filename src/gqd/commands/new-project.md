---
name: new-project
description: Initialize a new quantitative finance research project
---

<process>

## Initialize New Quantitative Finance Research Project

### Step 1: Create project structure
Create the `.gqd/` directory and all required subdirectories:
- `.gqd/` — project state and config
- `.gqd/observability/sessions/` — session logs
- `.gqd/traces/` — execution traces
- `knowledge/` — research knowledge base
- `data/` — market data and datasets
- `backtests/` — backtest results and reports
- `.scratch/` — temporary working files (gitignored)

### Step 2: Gather project information
Ask the user:
1. **Project name**: What is this research project about?
2. **Research question**: What specific quantitative finance question are you investigating?
3. **Domain**: Which area? (derivatives pricing, portfolio optimization, risk management, market microstructure, time series analysis, factor investing, etc.)
4. **Model profile**: pricing-theory (default), empirical, exploratory, backtesting, or paper-writing?
5. **Research mode**: explore, balanced (default), exploit, or adaptive?

### Step 3: Create initial ROADMAP.md
Based on the research question, create a phase breakdown:

```markdown
# [Project Name] — Roadmap

## Phase 1: Literature Survey
**Goal**: Identify known models, results, and data sources for [topic]

## Phase 2: Model Specification
**Goal**: Define the model, state all assumptions, lock conventions

## Phase 3: Analytical Derivation
**Goal**: Derive closed-form solutions or analytical approximations

## Phase 4: Numerical Implementation
**Goal**: Implement the model numerically (Monte Carlo, PDE, optimization)

## Phase 5: Backtesting and Empirical Validation
**Goal**: Validate model/strategy on historical data with proper methodology

## Phase 6: Robustness and Sensitivity
**Goal**: Test robustness across parameters, regimes, and specifications

## Phase 7: Paper Writing
**Goal**: Write publication-ready manuscript
```

Adjust phases based on the specific research question. Theoretical projects may skip backtesting; empirical projects may skip analytical derivation.

### Step 4: Initialize state
Create STATE.md and state.json with:
- Project name and creation date
- Phase listing from ROADMAP
- Phase 1 set as active
- Research mode and autonomy mode

### Step 5: Initialize config
Create `.gqd/config.json` with user's choices.

### Step 6: Initialize git
If not already a git repo, initialize one. Add `.scratch/` and `data/` to `.gitignore`.
Commit the initial project structure.

### Step 7: Convention prompting
Ask if the user wants to pre-set any conventions:
- Pricing model and assumptions
- Risk-free rate source and convention
- Return convention (log vs simple)
- Day count convention
- Data source

Lock any conventions the user specifies.

### Step 8: Summary
Display:
- Project structure created
- Phases from roadmap
- Active conventions
- Next step: run `plan-phase` to begin Phase 1

</process>
