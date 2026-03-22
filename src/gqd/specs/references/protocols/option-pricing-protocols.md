# Option Pricing Protocols

> Step-by-step methodology guides for derivatives pricing.

## Protocol: Black-Scholes Option Pricing

### When to Use
European options on non-dividend-paying stocks with constant volatility assumption.

### Steps
1. **State the assumptions explicitly**: GBM, constant vol, constant risk-free rate, no dividends, no transaction costs, continuous trading
2. **Specify the payoff**: max(S-K, 0) for calls, max(K-S, 0) for puts
3. **Apply the formula**: C = S*N(d1) - K*exp(-rT)*N(d2)
4. **Compute d1 and d2**: d1 = [ln(S/K) + (r + sigma^2/2)*T] / (sigma*sqrt(T))
5. **Verify put-call parity**: C - P = S - K*exp(-rT)
6. **Compute Greeks** analytically and verify numerically
7. **Check boundary conditions**: S >> K, S << K, T -> 0, sigma -> 0, sigma -> inf

### Common LLM Pitfalls
- Sign errors in d1/d2 (E001 compounding variant)
- Forgetting to adjust for dividends when they exist (E007)
- Using wrong annualization for sigma (E009)
- Applying to American options without noting early exercise premium

---

## Protocol: Stochastic Volatility Model Pricing (Heston)

### When to Use
When implied volatility smile/skew is important; pricing exotic or long-dated options.

### Steps
1. **State the model dynamics**: dS = mu*S*dt + sqrt(v)*S*dW_S, dv = kappa*(theta-v)*dt + xi*sqrt(v)*dW_v, corr(dW_S, dW_v) = rho
2. **Specify parameters**: kappa (mean reversion), theta (long-run variance), xi (vol of vol), rho (correlation), v0 (initial variance)
3. **Check Feller condition**: 2*kappa*theta > xi^2 (ensures variance stays positive)
4. **Apply characteristic function approach** for European options
5. **Implement numerical integration** for the inverse Fourier transform (Carr-Madan, COS method, or direct)
6. **Calibrate to market data**: minimize distance between model and market implied vols
7. **Verify**: put-call parity, boundary conditions, vol surface arbitrage-free

### Common LLM Pitfalls
- Feller condition not checked (variance can hit zero)
- Numerical instability in characteristic function evaluation (use Roger Lee's moment formula for large strikes)
- Incorrect correlation sign convention (rho < 0 produces skew)
- Calibration overfitting to smile shape at the expense of term structure

---

## Protocol: Monte Carlo Option Pricing

### When to Use
Path-dependent options, complex payoffs, high-dimensional problems where analytical solutions don't exist.

### Steps
1. **Specify the dynamics** under risk-neutral measure Q
2. **Choose discretization scheme**: Euler-Maruyama, Milstein, exact simulation where possible
3. **Implement variance reduction**: antithetic variates, control variates (use Black-Scholes price as control), importance sampling
4. **Set number of paths**: start with 10K, increase until standard error is acceptable
5. **Report**: price estimate, standard error, 95% confidence interval
6. **Convergence check**: price should converge as N_paths increases (plot price vs 1/sqrt(N))
7. **Benchmark**: compare with analytical price where available (e.g., European options)

### Common LLM Pitfalls
- Simulating under P measure instead of Q measure (missing risk-neutral drift)
- Euler discretization bias for mean-reverting processes (use exact simulation for GBM, log-Euler for Heston)
- Not reporting standard errors (point estimate without uncertainty is meaningless)
- Incorrect variance reduction implementation (antithetic must use SAME uniform randoms)

---

## Protocol: Implied Volatility Surface Construction

### When to Use
Building a volatility surface from market option prices for pricing, hedging, or risk management.

### Steps
1. **Collect market data**: bid/ask for calls and puts across strikes and maturities
2. **Filter data**: remove stale quotes, verify put-call parity, remove obvious errors
3. **Invert Black-Scholes** for each option to get implied vol (Newton-Raphson or Brent's method)
4. **Interpolate**: across strikes (spline, SABR parameterization) and maturities (flat forward variance)
5. **Check for arbitrage**: no butterfly arbitrage (d^2C/dK^2 >= 0), no calendar arbitrage (total variance increasing in T)
6. **Extrapolate** wings carefully: use Roger Lee's moment formula for far wings
7. **Validate**: reprice liquid options from the surface, check residuals

### Common LLM Pitfalls
- Butterfly arbitrage in interpolated surface (non-convex call prices in strike)
- Calendar arbitrage (total implied variance decreasing in maturity)
- Using mid prices instead of proper bid/ask handling
- Implied vol solver not converging for deep ITM/OTM options
