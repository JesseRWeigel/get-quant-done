# Fixed Income Protocols

> Step-by-step methodology guides for fixed income analysis and valuation.

## Protocol: Duration and Convexity Analysis

### When to Use
Measuring and managing interest rate sensitivity of bonds and bond portfolios.

### Steps
1. **Compute Macaulay duration** — D_Mac = (1/P) × Σ t × CF_t / (1+y)^t, the weighted-average time to receive cash flows
2. **Compute modified duration** — D_mod = D_Mac / (1 + y/k), where k = compounding frequency; this measures the percentage price change for a 1% yield change: ΔP/P ≈ −D_mod × Δy
3. **Compute effective (option-adjusted) duration** — D_eff = (P₋ − P₊) / (2 × P₀ × Δy), using full repricing with a term structure model; required for callable/putable bonds, MBS, and structured products
4. **Compute convexity** — C = (P₋ + P₊ − 2P₀) / (P₀ × Δy²); the second-order correction: ΔP/P ≈ −D_mod × Δy + ½ × C × Δy²
5. **For portfolios**: portfolio duration = Σ w_i × D_i (market-value weighted); portfolio convexity = Σ w_i × C_i
6. **Assess key rate durations** — sensitivity to specific points on the yield curve (e.g., 2Y, 5Y, 10Y, 30Y) to capture non-parallel curve movements
7. **Hedge using duration matching** — match portfolio duration to the benchmark or target; use convexity matching for large rate moves
8. **Report** — duration, convexity, key rate durations, and the DV01 (dollar value of a basis point = D_mod × P × 0.0001)

### Common LLM Pitfalls
- Using modified duration for bonds with embedded options (requires effective duration from a term structure model)
- Ignoring convexity for large yield changes (duration alone overestimates price decline and underestimates price increase)
- Computing portfolio duration as a simple average instead of market-value-weighted average
- Confusing Macaulay duration (in years) with modified duration (percentage price sensitivity)

---

## Protocol: Term Structure Modeling (Vasicek, CIR, HJM)

### When to Use
Modeling the dynamics of the yield curve for pricing, hedging, and risk management of interest rate derivatives.

### Steps
1. **Choose the model class**:
   - **Short-rate models**: Vasicek (mean-reverting, Gaussian, allows negative rates), CIR (mean-reverting, non-negative rates, square-root diffusion), Hull-White (time-dependent parameters, fits initial term structure)
   - **HJM framework**: models the entire forward rate curve; requires specifying the volatility function σ(t,T) of instantaneous forward rates
2. **For Vasicek** (dr = κ(θ−r)dt + σdW): estimate κ (mean reversion speed), θ (long-run mean), σ (volatility) from historical short rates or from bond prices
3. **For CIR** (dr = κ(θ−r)dt + σ√r dW): same parameters but the volatility scales with √r; verify the Feller condition 2κθ > σ² (ensures r stays positive)
4. **For HJM**: specify the volatility structure (constant → Ho-Lee; exponentially decaying → Hull-White extended Vasicek); derive the drift from the no-arbitrage drift restriction: μ(t,T) = σ(t,T) × ∫_t^T σ(t,s)ds
5. **Calibrate to market data** — fit model parameters to observed zero-coupon yields, swap rates, or swaption volatilities using least squares or maximum likelihood
6. **Price derivatives** — use the calibrated model to price caps, floors, swaptions via analytical formulas (Vasicek, CIR) or Monte Carlo simulation (HJM)
7. **Validate** — compare model-implied prices to market prices for instruments not used in calibration (out-of-sample test)
8. **Report model limitations** — Vasicek allows negative rates (feature or bug depending on the rate environment); CIR cannot fit humped volatility structures; single-factor models cannot capture curve twists

### Common LLM Pitfalls
- Using Vasicek when negative rates are not acceptable (CIR guarantees non-negativity if Feller condition holds)
- Forgetting the HJM drift restriction (the drift is determined by the volatility function under no-arbitrage)
- Calibrating to the initial term structure without recalibrating periodically (parameters drift)
- Confusing the physical (P) and risk-neutral (Q) measures when interpreting parameters (mean reversion speed and long-run mean differ under P and Q)

---

## Protocol: Credit Risk Modeling

### When to Use
Measuring and managing the risk of default or credit quality deterioration in fixed income portfolios.

### Steps
1. **Choose the modeling approach**:
   - **Structural models** (Merton): default occurs when firm value falls below debt face value at maturity; equity = call option on firm assets; credit spread derived from put option
   - **Reduced-form models** (Jarrow-Turnbull, Duffie-Singleton): default is a surprise event driven by a hazard rate λ(t); no explicit modeling of firm value
2. **For structural models**: estimate firm asset value V and volatility σ_V from equity value and equity volatility (using the Merton system of equations); compute distance to default DD = (ln(V/D) + (μ − σ²_V/2)T) / (σ_V √T)
3. **For reduced-form models**: extract hazard rates from CDS spreads: s ≈ λ × (1 − R), where R = recovery rate; or from bond credit spreads
4. **Estimate recovery rates** — historical averages by seniority (senior secured ~65%, senior unsecured ~45%, subordinated ~30%) or use market-implied recovery from CDS
5. **Compute expected loss** — EL = PD × LGD × EAD (probability of default × loss given default × exposure at default)
6. **For portfolio credit risk**: model default correlation using copulas (Gaussian copula, t-copula) or factor models; compute portfolio loss distribution
7. **Compute credit VaR** — the quantile of the portfolio loss distribution at the desired confidence level; credit VaR = unexpected loss at the α quantile minus expected loss
8. **Stress test** — apply scenarios with elevated default rates, reduced recovery, and increased correlation

### Common LLM Pitfalls
- Applying the Gaussian copula without recognizing its limitations in capturing tail dependence (notoriously underestimates joint defaults in crises)
- Confusing risk-neutral PD (from market prices) with physical PD (from historical default rates) — risk-neutral PD is higher due to the risk premium
- Using constant recovery rates when recovery is correlated with default (in systemic crises, recovery drops when defaults rise)
- Treating credit ratings as sufficient statistics for default probability (ratings are ordinal and lag market-implied measures)

---

## Protocol: Bond Relative Value Analysis

### When to Use
Identifying mispriced bonds by comparing observed yields/spreads to theoretical fair values.

### Steps
1. **Compute the Z-spread** — the constant spread added to the Treasury zero curve that reprices the bond; Z-spread captures credit and liquidity premia
2. **Compute the OAS (option-adjusted spread)** — for bonds with embedded options, use a term structure model to remove the option value; OAS = Z-spread minus the option cost
3. **Compare to peer group** — plot OAS against duration, credit rating, sector, and issuer for comparable bonds; identify outliers
4. **Assess the richness/cheapness** — a bond is "cheap" if its OAS is wider than peers with similar risk, "rich" if tighter
5. **Decompose the spread** — credit component (from CDS or rating-matched index), liquidity component (bid-ask, issue size, age), and residual (potential mispricing)
6. **Check for structural reasons** — index inclusion/exclusion, regulatory constraints (bank capital rules), supply/demand imbalances, tax effects
7. **Execute the trade** — buy cheap bonds, sell rich bonds in a duration-neutral pair or against the CDS
8. **Monitor convergence** — track the spread differential over time; define stop-loss and take-profit levels

### Common LLM Pitfalls
- Comparing OAS across bonds with different embedded option types (callable vs putable vs MBS prepayment)
- Ignoring liquidity as an explanation for apparent cheapness (illiquid bonds trade wide for a reason)
- Using nominal spread instead of Z-spread or OAS for bonds with non-bullet cash flows
- Not duration-matching the long and short legs of a relative value trade
