# Get Quant Done

> An AI copilot for autonomous quantitative finance research — from hypothesis to backtested strategy to publication-ready paper.

**Inspired by [Get Physics Done](https://github.com/psi-oss/get-physics-done)** — the open-source AI copilot that autonomously conducts physics research. Get Quant Done adapts GPD's architecture for quantitative finance and financial economics research.

## Vision

Quantitative finance demands both mathematical rigor and empirical validation. A pricing model that violates no-arbitrage, a strategy that survives out-of-sample testing, a risk measure that satisfies coherence axioms — these are verifiable properties that an AI system can check systematically.

Get Quant Done wraps LLM capabilities in a verification-first framework that:
- **Locks model assumptions** across phases (pricing model, discount rate convention, risk measure definitions, distribution assumptions)
- **Verifies financial consistency** — no-arbitrage conditions, put-call parity, Greeks consistency, conservation of portfolio value
- **Decomposes research** into phases: literature survey → model specification → analytical derivation → numerical implementation → backtesting → robustness checks → paper writing
- **Prevents common LLM errors** — compounding mistakes, distribution assumption failures, survivorship bias, look-ahead bias

## Architecture

Adapted from GPD's three-layer design:

### Layer 1 — Core Library (Python)
State management, phase lifecycle, git operations, convention locks, verification kernel.

### Layer 2 — MCP Servers
- `gqd-state` — Project state queries
- `gqd-conventions` — Financial model assumption locks
- `gqd-protocols` — Methodology protocols (option pricing, portfolio optimization, time series analysis, risk management, etc.)
- `gqd-patterns` — Cross-project learned patterns
- `gqd-verification` — Financial consistency and empirical validity checks
- `gqd-errors` — Known LLM quantitative finance failure modes

### Layer 3 — Agents & Commands
- `gqd-planner` — Research task decomposition
- `gqd-executor` — Model derivation and implementation
- `gqd-verifier` — Financial consistency verification
- `gqd-researcher` — Literature and data source discovery
- `gqd-backtester` — Strategy backtesting and robustness analysis
- `gqd-paper-writer` — Journal manuscript generation
- `gqd-referee` — Multi-perspective review (academic rigor, practitioner relevance, regulatory compliance)

## Convention Lock Fields

1. Pricing model (Black-Scholes, Heston, SABR, etc.)
2. Risk-free rate convention (continuously compounded, discrete, source)
3. Day count convention (ACT/360, ACT/365, 30/360)
4. Distribution assumptions (normal, log-normal, fat-tailed)
5. Risk measure (VaR confidence level, ES, coherent measures)
6. Return convention (simple, log, excess)
7. Benchmark definition
8. Transaction cost model
9. Rebalancing frequency
10. Data source and cleaning methodology

## Verification Framework

1. **No-arbitrage** — pricing models satisfy no-arbitrage conditions
2. **Put-call parity** — option prices consistent
3. **Greeks consistency** — numerical Greeks match analytical where available
4. **Boundary conditions** — model satisfies known limits (deep ITM/OTM, expiry)
5. **Distribution validity** — assumed distributions consistent with data
6. **Backtest integrity** — no look-ahead bias, survivorship bias, or data snooping
7. **Out-of-sample performance** — results hold outside training period
8. **Risk measure coherence** — subadditivity, monotonicity, translation invariance, positive homogeneity
9. **Conservation laws** — portfolio value, P&L attribution completeness
10. **Statistical significance** — t-stats, Sharpe confidence intervals, multiple testing corrections
11. **Literature comparison** — results compared with published benchmarks
12. **Robustness** — sensitivity to parameter choices, data windows, market regimes

## Status

**Early development** — Building core infrastructure. Contributions welcome!

## Relationship to GPD

We plan to showcase this in the [GPD Discussion Show & Tell](https://github.com/psi-oss/get-physics-done/discussions) once operational.

## Getting Started

```bash
# Coming soon
npx get-quant-done
```

## Contributing

We're looking for contributors with:
- Quantitative finance research or practice experience
- Financial mathematics background
- Backtesting framework experience (Python: backtrader, zipline, etc.)
- Familiarity with GPD's architecture

See the [Issues](../../issues) for specific tasks.

## License

MIT
