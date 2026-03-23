# Portfolio Optimization Protocols

> Step-by-step methodology guides for portfolio construction and optimization.

## Protocol: Mean-Variance Optimization

### When to Use
Constructing portfolios on the efficient frontier using expected returns, variances, and covariances.

### Steps
1. **Estimate the inputs** — expected returns vector μ (N×1), covariance matrix Σ (N×N) from historical data, factor models, or Bayesian priors
2. **Verify Σ is positive semi-definite** — check eigenvalues; if negative eigenvalues exist from estimation noise, apply nearest PSD matrix correction (Higham algorithm) or shrinkage
3. **Formulate the optimization** — min w'Σw subject to w'μ ≥ target return, w'1 = 1, and any constraints (long-only: w ≥ 0, position limits, sector constraints)
4. **Solve using quadratic programming** — this is a convex QP with linear constraints; use an appropriate solver (CVXPY, OSQP, Gurobi)
5. **Trace the efficient frontier** — solve for a range of target returns to obtain the full frontier; identify the tangency portfolio (maximum Sharpe ratio)
6. **Compute the tangency portfolio** — max (w'μ − r_f) / √(w'Σw) where r_f is the risk-free rate
7. **Perform sensitivity analysis** — perturb inputs by ±1 standard error and re-optimize; report how weights change (Michaud resampling or bootstrap)
8. **Report the solution** — optimal weights, expected return, expected volatility, Sharpe ratio, and the condition number of Σ

### Common LLM Pitfalls
- Using sample covariance matrices without shrinkage (leads to extreme, unstable weights — Ledoit-Wolf shrinkage is standard)
- Treating expected returns as known quantities rather than noisy estimates (mean-variance is highly sensitive to μ)
- Ignoring transaction costs, turnover constraints, and rebalancing frequency
- Reporting the efficient frontier without noting that it is an in-sample artifact and will degrade out-of-sample

---

## Protocol: Risk Parity Portfolio Construction

### When to Use
Building portfolios where each asset contributes equally to total portfolio risk, avoiding concentration in high-risk assets.

### Steps
1. **Define the risk contribution** — for asset i, RC_i = w_i × (Σw)_i / √(w'Σw), which is asset i's marginal contribution times its weight
2. **Set the target** — equal risk contribution: RC_i = (1/N) × σ_portfolio for all i
3. **Solve the optimization** — minimize Σ_i (RC_i − RC_target)² subject to w ≥ 0, w'1 = 1; this is non-convex but has a unique solution for PSD Σ
4. **Use the analytical shortcut** for the unconstrained case — w_i ∝ 1/σ_i when correlations are equal; otherwise use iterative solvers (Spinu 2013, Griveau-Billion et al. 2013)
5. **Apply leverage** — risk parity portfolios are typically low-volatility; lever to the target volatility or benchmark volatility using futures or margin
6. **Verify the risk decomposition** — confirm each asset's risk contribution is within tolerance of the target (e.g., ±5% of 1/N)
7. **Compare to alternatives** — benchmark against 1/N (equal weight), market cap weight, and mean-variance to demonstrate the diversification benefit

### Common LLM Pitfalls
- Confusing equal weight with equal risk contribution (they are the same only when all assets have identical risk)
- Ignoring leverage costs when scaling risk parity to a target volatility
- Using only volatility without accounting for correlations (risk parity requires the full covariance matrix)
- Not addressing the fact that risk parity can underperform when return-to-risk ratios vary significantly across assets

---

## Protocol: Black-Litterman Model

### When to Use
Combining market equilibrium returns with investor views to produce stable, intuitive portfolio weights.

### Steps
1. **Compute equilibrium excess returns** — π = δΣw_mkt, where δ = risk aversion coefficient (typically derived from market Sharpe ratio), Σ = covariance matrix, w_mkt = market capitalization weights
2. **Specify investor views** — express as P·μ = Q + ε, where P is the pick matrix (K×N), Q is the view vector (K×1), and Ω = diag(τ·P·Σ·P') is the uncertainty of views
3. **Set the scalar τ** — typically 0.025 to 0.05 (represents uncertainty in the equilibrium prior relative to the covariance)
4. **Compute the posterior** — E[μ] = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ × [(τΣ)⁻¹π + P'Ω⁻¹Q]
5. **Derive optimal weights** — apply mean-variance optimization with the posterior expected returns and posterior covariance
6. **Verify that with zero views, weights converge to market weights** — this is the key sanity check for Black-Litterman
7. **Perform view sensitivity analysis** — vary confidence in views (Ω) and observe how weights change; high-conviction views should shift weights more
8. **Report the tilts** — show deviations from market-cap weights and link each tilt to the corresponding view

### Common LLM Pitfalls
- Setting τ too large (e.g., 1.0), which makes the prior irrelevant and reduces Black-Litterman to standard mean-variance
- Forgetting to compute equilibrium returns from market-cap weights (using historical returns as the prior defeats the purpose)
- Specifying views without proper uncertainty calibration in Ω
- Not verifying the zero-view case produces market-cap weights

---

## Protocol: Robust Portfolio Optimization

### When to Use
Constructing portfolios that are resilient to estimation error in expected returns and covariances.

### Steps
1. **Quantify the uncertainty** — define uncertainty sets for μ (e.g., ellipsoidal: ‖μ − μ̂‖_Σ ≤ κ) and Σ (e.g., box: each σ_ij within confidence bounds)
2. **Formulate the robust counterpart** — max-min: maximize the worst-case return over the uncertainty set, or min-max: minimize the worst-case risk
3. **For ellipsoidal uncertainty in μ**: the robust problem reduces to min w'Σw + κ√(w'Σw) subject to w'μ̂ ≥ target + κ√(w'Σw), which is a second-order cone program (SOCP)
4. **Solve the SOCP** — use CVXPY, MOSEK, or ECOS; verify feasibility and solution status
5. **Compare to non-robust solution** — robust portfolios will be more diversified and less sensitive to estimation errors, but may sacrifice expected return
6. **Tune the robustness parameter κ** — too small reduces to standard MVO, too large produces overly conservative (near-cash) portfolios; calibrate κ to the estimation error magnitude
7. **Backtest both robust and non-robust portfolios** — compare out-of-sample Sharpe ratios, turnover, and maximum drawdown
8. **Report the worst-case metrics** — worst-case return, worst-case Sharpe ratio over the uncertainty set

### Common LLM Pitfalls
- Making the uncertainty set too large (produces trivially conservative portfolios)
- Forgetting that robust optimization addresses estimation error, not market risk
- Not comparing the robust solution to simpler alternatives (1/N, shrinkage) that also address estimation error
- Treating the robust optimal portfolio as truly "optimal" rather than as a hedge against the worst case within the assumed uncertainty set
