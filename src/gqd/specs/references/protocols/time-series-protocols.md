# Time Series Protocols

> Step-by-step methodology guides for financial time series modeling and analysis.

## Protocol: ARIMA Model Selection and Estimation

### When to Use
Modeling and forecasting univariate time series data with potential trends and autocorrelation.

### Steps
1. **Plot the series and ACF/PACF** — visual inspection for trends, seasonality, and stationarity
2. **Test for stationarity** — apply ADF (Augmented Dickey-Fuller), KPSS, or Phillips-Perron tests. ADF H₀: unit root; KPSS H₀: stationarity. Use both for confirmation
3. **Difference to achieve stationarity** — if non-stationary, take first differences (d=1); for seasonal data, seasonal differences. The order d is the integration order in ARIMA(p,d,q)
4. **Identify p and q** — use ACF (cuts off at lag q for MA) and PACF (cuts off at lag p for AR) patterns; confirm with information criteria (AIC, BIC) over a grid of (p,q) values
5. **Estimate the model** — maximum likelihood estimation; verify that all AR roots lie outside the unit circle (stationarity) and MA roots lie outside the unit circle (invertibility)
6. **Diagnose residuals** — Ljung-Box test for remaining autocorrelation, check normality (QQ plot), check for ARCH effects (Engle's ARCH test) — if present, consider GARCH
7. **Forecast** — generate point forecasts and prediction intervals; note that prediction intervals widen with horizon
8. **Validate out-of-sample** — use rolling or expanding window forecasts; compare RMSE/MAE to naive benchmarks (random walk, seasonal naive)

### Common LLM Pitfalls
- Over-differencing (d > 2 is almost never appropriate and introduces spurious autocorrelation)
- Selecting model order by ACF/PACF alone without information criteria confirmation
- Interpreting ADF failure to reject as "the series is stationary" (ADF tests for a unit root, not stationarity)
- Reporting in-sample fit as forecasting accuracy without out-of-sample validation

---

## Protocol: GARCH Volatility Modeling

### When to Use
Modeling time-varying volatility (heteroskedasticity) in financial return series.

### Steps
1. **Verify ARCH effects exist** — apply Engle's ARCH-LM test to the return series or residuals from a mean model; examine the ACF of squared returns
2. **Specify the mean equation** — ARMA model for returns, or a constant mean if returns are approximately uncorrelated
3. **Choose the GARCH variant** — GARCH(1,1) is the standard starting point; consider EGARCH (asymmetric, no parameter constraints), GJR-GARCH (leverage effect), or TGARCH
4. **Estimate the model** — quasi-maximum likelihood (QMLE) with a Student-t or skewed-t innovation distribution (financial returns are fat-tailed)
5. **Check parameter constraints** — for GARCH(1,1): α₀ > 0, α₁ ≥ 0, β₁ ≥ 0, and α₁ + β₁ < 1 (covariance stationarity). If α₁ + β₁ ≈ 1, consider IGARCH
6. **Compute the persistence** — α₁ + β₁ measures volatility persistence; values near 1 indicate long memory in volatility
7. **Generate volatility forecasts** — multi-step forecasts revert to the unconditional variance σ² = α₀ / (1 − α₁ − β₁) at a rate governed by persistence
8. **Validate with VaR backtesting** — use the conditional volatility to compute VaR; backtest with Kupiec and Christoffersen tests

### Common LLM Pitfalls
- Fitting GARCH to price levels instead of returns (GARCH models stationary variance dynamics)
- Using Gaussian innovations when the data are clearly fat-tailed (produces biased VaR)
- Ignoring the leverage effect in equity returns (negative returns increase volatility more than positive returns — use EGARCH or GJR)
- Confusing the conditional variance forecast with the unconditional (long-run) variance

---

## Protocol: Cointegration and Error Correction

### When to Use
Modeling long-run equilibrium relationships between non-stationary time series (e.g., pairs trading, yield curve factors).

### Steps
1. **Confirm each series is I(1)** — apply unit root tests (ADF, KPSS) to each series individually; both must be non-stationary in levels but stationary in first differences
2. **Test for cointegration** — Engle-Granger two-step (regress Y on X, test residuals for stationarity) or Johansen trace/maximum eigenvalue test (for multivariate systems)
3. **For Engle-Granger**: estimate the cointegrating regression Y_t = α + βX_t + ε_t, then test ε̂_t for a unit root using critical values from Engle-Granger tables (NOT standard ADF tables)
4. **For Johansen**: specify the VAR lag order, select the deterministic trend specification (none, restricted constant, unrestricted constant, restricted trend), determine the cointegration rank r
5. **Estimate the VECM** — ΔY_t = αβ'Y_{t-1} + Σ Γ_i ΔY_{t-i} + ε_t, where α = adjustment speeds, β = cointegrating vector, Γ = short-run dynamics
6. **Interpret the error correction term** — α measures how fast deviations from equilibrium are corrected; both series should adjust (or explain why one does not)
7. **Validate the cointegrating relationship** — is it economically meaningful? Does it remain stable in sub-samples?
8. **Use for forecasting or trading** — deviations from the cointegrating relationship signal mean-reversion opportunities

### Common LLM Pitfalls
- Using standard ADF critical values for the Engle-Granger test (cointegration residual tests require different critical values)
- Running OLS on non-stationary series without testing for cointegration (spurious regression)
- Confusing correlation with cointegration (highly correlated series need not be cointegrated, and vice versa)
- Forgetting to check that the cointegrating relationship is stable over time (structural breaks can destroy cointegration)

---

## Protocol: Regime Switching Models

### When to Use
Modeling time series that exhibit distinct behavioral regimes (e.g., bull/bear markets, high/low volatility states).

### Steps
1. **Specify the number of regimes** — start with 2 (most common for financial data: expansion/recession or low-vol/high-vol); test 3 regimes if economically motivated
2. **Choose the model** — Markov-switching mean (Hamilton 1989), Markov-switching variance, or both; specify the state-dependent parameters
3. **Estimate via EM algorithm or MLE** — the likelihood involves the Hamilton filter (forward algorithm) to compute filtered state probabilities
4. **Extract the regime probabilities** — filtered P(S_t = j | data up to t) and smoothed P(S_t = j | all data) probabilities for each time point
5. **Interpret the transition matrix** — P[S_{t+1} = j | S_t = i] gives regime persistence; high diagonal values mean persistent regimes
6. **Compute expected regime durations** — 1/(1 − p_ii) is the expected duration in regime i
7. **Validate regime identification** — do the identified regimes correspond to known economic events (recessions, crises)?
8. **Use for risk management** — regime-conditional VaR and portfolio allocation can adapt to the current regime

### Common LLM Pitfalls
- Using too many regimes without economic justification (over-fitting; 2 regimes is usually sufficient)
- Applying standard likelihood ratio tests for the number of regimes (the null has nuisance parameters under the alternative, invalidating standard chi-squared tests — use Hansen's bootstrap or information criteria)
- Confusing filtered and smoothed probabilities (filtered uses information up to t; smoothed uses the full sample)
- Ignoring estimation uncertainty in regime assignments when making trading decisions
