# Known LLM Quantitative Finance Failure Modes

> This catalog documents systematic failure patterns of LLMs in quantitative finance reasoning.
> The verifier and plan-checker cross-reference against these patterns.

## Critical Errors (High Frequency)

### E001: Compounding Errors
**Pattern**: Confusing simple and continuously compounded returns, or applying the wrong compounding convention.
**Example**: Using r_simple where ln(1+r) is required, computing annualized Sharpe as mean/std*sqrt(252) with simple returns instead of log returns.
**Guard**: Explicitly state compounding convention at every step. Cross-check: for small r, simple and log returns should approximately agree.

### E002: Distribution Assumption Failures
**Pattern**: Assuming normal returns when fat tails, skewness, or volatility clustering are present.
**Example**: Using VaR = mu - z*sigma (Gaussian) when returns have excess kurtosis > 3, leading to severe underestimation of tail risk.
**Guard**: Always test distributional assumptions (KS test, QQ plot, Jarque-Bera). Report kurtosis and skewness.

### E003: Survivorship Bias
**Pattern**: Backtesting on a universe that only includes currently existing securities.
**Example**: Testing a momentum strategy on current S&P 500 constituents — excludes companies that went bankrupt (which momentum would have held).
**Guard**: Use point-in-time constituent lists. Document data source and whether delistings are included.

### E004: Look-Ahead Bias
**Pattern**: Using information not available at decision time.
**Example**: Using revised GDP figures instead of advance estimates, using end-of-day prices to generate signals acted upon at the open, using full-sample statistics for normalization.
**Guard**: Implement strict point-in-time data access. Log the timestamp of every data point used.

### E005: Overfitting / Data Snooping
**Pattern**: Testing many parameter combinations on the same data without correction.
**Example**: Testing 100 moving average crossover combinations, reporting the best one as "the strategy." With 100 tests at 5% significance, expect ~5 false positives.
**Guard**: Apply multiple testing corrections (Bonferroni, BH). Report number of configurations tested. Use true out-of-sample validation.

## Serious Errors (Medium Frequency)

### E006: Incorrect Day Count Convention
**Pattern**: Mixing day count conventions when computing yields, accrued interest, or discount factors.
**Example**: Using ACT/365 for a USD money market instrument (should be ACT/360), producing incorrect discount factors.
**Guard**: Lock the day count convention and verify it matches instrument type and market convention.

### E007: Discrete vs Continuous Dividend Handling
**Pattern**: Using continuous dividend yield when discrete dividends are paid, or vice versa.
**Example**: In Black-Scholes, using q as continuous dividend yield for a stock that pays quarterly dividends of known amounts, producing incorrect put-call parity.
**Guard**: Specify dividend model explicitly. For known discrete dividends, adjust spot price.

### E008: Wrong Risk-Free Rate
**Pattern**: Using an inappropriate risk-free rate proxy.
**Example**: Using the 10-year Treasury yield as risk-free rate for a 1-month option (should match option maturity), or using nominal rates for real return calculations.
**Guard**: Risk-free rate must match: maturity, currency, and compounding convention of the instrument being priced.

### E009: Annualization Errors
**Pattern**: Incorrect conversion between different frequencies.
**Example**: Annualizing daily volatility as sigma*sqrt(365) instead of sigma*sqrt(252) for business-day data, or annualizing monthly Sharpe as SR_monthly*sqrt(12) without checking for autocorrelation.
**Guard**: State the number of periods per year explicitly. For Sharpe ratio, check for return autocorrelation (Lo, 2002 correction).

### E010: P&L Attribution Errors
**Pattern**: P&L components don't sum to total P&L.
**Example**: Decomposing option P&L into delta, gamma, theta, vega, and "residual" — but residual is larger than any single Greek component, indicating the decomposition is wrong.
**Guard**: Always verify: sum of P&L components = total P&L. If residual exceeds 10% of total, investigate.

## Moderate Errors (Common but Usually Caught)

### E011: Misapplied No-Arbitrage Arguments
**Pattern**: Claiming an arbitrage exists when it doesn't (or missing one that does).
**Example**: Claiming a calendar spread is an arbitrage without accounting for the cost of carry, or missing a butterfly arbitrage in an interpolated vol surface.
**Guard**: For each claimed arbitrage: specify the exact trades, initial cost, and guaranteed payoff. For no-arbitrage claims: verify all necessary conditions.

### E012: Incorrect Greeks Computation
**Pattern**: Computing Greeks incorrectly, especially for exotic options or stochastic vol models.
**Example**: Computing delta as dC/dS using a bump-and-revalue but bumping implied vol instead of keeping it constant (sticky-strike vs sticky-delta).
**Guard**: Specify what is held constant when computing each Greek. Compare with analytical formula where available.

### E013: Ignoring Transaction Costs
**Pattern**: Claiming a strategy is profitable but ignoring realistic execution costs.
**Example**: A high-frequency mean-reversion strategy with 0.01% expected return per trade but 0.05% round-trip transaction costs.
**Guard**: Always report gross and net-of-cost performance. Include realistic estimates of spread, slippage, and market impact.

### E014: Correlation vs Causation
**Pattern**: Interpreting a predictive relationship as causal.
**Example**: "High VIX predicts high future returns" treated as a causal mechanism rather than a statistical regularity that may break down.
**Guard**: Clearly distinguish predictive (statistical) from causal claims. Test for spurious correlation (common trends, confounders).

### E015: Stationarity Assumptions
**Pattern**: Assuming return distributions or correlations are stationary when they change over time.
**Example**: Using a single correlation matrix estimated over 10 years for portfolio optimization, when correlations spike during crises.
**Guard**: Test for stationarity (ADF test, rolling statistics). Use regime-switching models or rolling windows where appropriate.

## How to Use This Catalog

1. **Plan-checker**: Before execution, identify tasks where specific errors are likely. Add explicit guards.
2. **Executor**: Consult relevant entries when performing work of that type. Follow guards.
3. **Verifier**: After execution, cross-reference results against applicable error patterns.
4. **Pattern library**: When a new error pattern is discovered, add it here.
