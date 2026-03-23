# Risk Management Protocols

> Step-by-step methodology guides for financial risk measurement and management.

## Protocol: Value at Risk (VaR) Estimation

### When to Use
Estimating the maximum loss at a given confidence level over a specified holding period.

### Steps
1. **Define the parameters** — confidence level (95% or 99%), holding period (1-day, 10-day), portfolio composition
2. **Choose the method**:
   - **Historical simulation**: sort historical P&L, VaR = the (1−α) quantile. Non-parametric, no distribution assumption
   - **Parametric (variance-covariance)**: VaR = μ − z_α × σ. Assumes normality, uses portfolio volatility from the covariance matrix
   - **Monte Carlo simulation**: simulate N price paths from a fitted model, compute portfolio P&L, take the (1−α) quantile
3. **For historical simulation**: choose the lookback window (250–500 days typical); consider EWMA-weighted historical simulation for recency bias
4. **For parametric VaR**: estimate σ using EWMA (RiskMetrics) or GARCH; adjust for fat tails using Student-t or Cornish-Fisher expansion
5. **Scale across holding periods** — √T rule for scaling 1-day VaR to T-day VaR (valid only under i.i.d. assumption; for autocorrelated series, adjust)
6. **Backtest the VaR model** — count exceptions (days where loss exceeds VaR); apply Kupiec unconditional coverage test and Christoffersen conditional coverage test (independence of exceptions)
7. **Report VaR alongside Expected Shortfall** — VaR alone does not capture tail risk beyond the threshold
8. **Document model limitations** — VaR is not subadditive (portfolio VaR can exceed sum of component VaRs), non-coherent risk measure

### Common LLM Pitfalls
- Applying the √T scaling rule to fat-tailed or autocorrelated returns (underestimates multi-day risk)
- Using normal distribution for parametric VaR without adjusting for fat tails (underestimates tail risk)
- Reporting VaR as the maximum possible loss (it is the loss at a specific confidence level, not the worst case)
- Not backtesting the VaR model against realized losses

---

## Protocol: Expected Shortfall (Conditional VaR)

### When to Use
Measuring the expected loss conditional on exceeding VaR — captures tail risk and is a coherent risk measure.

### Steps
1. **Define ES** — ES_α = E[Loss | Loss > VaR_α] = average of all losses beyond the VaR threshold
2. **Compute from historical simulation** — average the worst (1−α)% of P&L observations
3. **Compute from parametric model** — for normal: ES = μ + σ × φ(z_α)/(1−α), where φ is the standard normal PDF
4. **Compute from Monte Carlo** — average the worst (1−α)% of simulated P&L scenarios
5. **Verify coherence properties** — ES is subadditive (portfolio ES ≤ sum of component ES), positive homogeneous, translation invariant, and monotone
6. **Backtest ES** — use McNeil and Frey (2000) approach: test whether exceedances (conditional on exceeding VaR) have the correct expected magnitude; or use Acerbi-Szekely (2014) tests
7. **Use ES for risk budgeting** — decompose portfolio ES into component ES contributions (Euler decomposition): ES_i = w_i × ∂ES/∂w_i
8. **Compare to VaR** — ES is preferred by Basel III/IV for market risk capital (FRTB); ES at 97.5% is approximately equivalent to VaR at 99% for normal distributions

### Common LLM Pitfalls
- Computing ES as the VaR at a higher confidence level (ES is a conditional expectation, not a quantile)
- Forgetting that ES backtesting is fundamentally harder than VaR backtesting (requires estimating conditional expectations, not just counting exceptions)
- Using ES at 95% and comparing directly to VaR at 99% without adjustment
- Not recognizing that ES is more sensitive to extreme tail modeling assumptions

---

## Protocol: Stress Testing and Scenario Analysis

### When to Use
Evaluating portfolio resilience under extreme but plausible market conditions.

### Steps
1. **Define the purpose** — regulatory stress test (CCAR/DFAST), internal risk management, or client reporting
2. **Design historical scenarios** — identify past crisis events (2008 GFC, 2020 COVID, 1998 LTCM, 1987 Black Monday); apply the observed risk factor changes to the current portfolio
3. **Design hypothetical scenarios** — construct plausible-but-extreme scenarios: define shocks to key risk factors (equity indices −30%, credit spreads +300bps, rates +200bps, FX ±20%), apply cross-asset correlations consistent with the scenario narrative
4. **Apply reverse stress testing** — identify the scenarios that would cause a specified loss (e.g., what conditions would produce a loss > $X?); work backward from the loss to the scenario
5. **Compute portfolio impact** — full revaluation of all positions under each scenario; report P&L, VaR change, liquidity impact, margin calls
6. **Assess second-order effects** — funding stress, counterparty credit risk, margin spirals, liquidity evaporation
7. **Present results to management** — tabulate scenarios with portfolio loss, worst affected positions, risk limit breaches
8. **Define action plans** — for each scenario, specify hedging actions, position reductions, or capital reserves needed

### Common LLM Pitfalls
- Using only historical scenarios (past crises may not capture future risks — hypothetical scenarios are essential)
- Applying shocks to individual risk factors without maintaining cross-factor consistency (e.g., equity crash should be accompanied by credit spread widening and flight-to-quality in rates)
- Ignoring liquidity risk in stress tests (positions may not be liquidatable at marked prices during a crisis)
- Treating stress test results as VaR estimates (stress tests are specific scenarios, not probabilistic measures)

---

## Protocol: Risk Decomposition and Attribution

### When to Use
Decomposing portfolio risk into contributions from individual positions, asset classes, or risk factors.

### Steps
1. **Choose the risk measure** — volatility, VaR, ES, or tracking error
2. **Compute marginal risk contributions** — MRC_i = ∂Risk/∂w_i (partial derivative of the portfolio risk with respect to the weight of asset i)
3. **Compute component risk contributions** — CRC_i = w_i × MRC_i; by Euler's theorem for homogeneous functions, Σ CRC_i = total portfolio risk
4. **Express as percentage contributions** — %CRC_i = CRC_i / total risk × 100; this identifies the top risk contributors
5. **For factor-based decomposition** — decompose returns into factor exposures (β) and residual: R_p = Σ β_j F_j + ε; risk = β'Σ_F β + σ²_ε
6. **Attribute risk changes over time** — when portfolio risk changes, decompose into: allocation effect (weight changes × old risk), selection effect (old weights × risk changes), and interaction effect
7. **Validate** — component risk contributions must sum to total risk; check against full portfolio revaluation
8. **Report** — rank positions/factors by risk contribution; identify diversification benefit (sum of standalone risks − portfolio risk)

### Common LLM Pitfalls
- Confusing standalone risk (risk of the position in isolation) with component risk contribution (risk within the portfolio context)
- Forgetting that marginal risk contributions depend on the covariance structure (a high-volatility asset may have low marginal risk if negatively correlated with the portfolio)
- Using Euler decomposition for non-homogeneous risk measures (it requires positive homogeneity of degree 1)
- Not distinguishing between risk contribution and performance attribution (risk looks at variability, performance looks at returns)
