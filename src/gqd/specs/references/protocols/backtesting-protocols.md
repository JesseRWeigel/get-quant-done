# Backtesting Protocols

> Step-by-step methodology guides for strategy backtesting and empirical validation.

## Protocol: Cross-Sectional Strategy Backtest

### When to Use
Testing long-short strategies that rank securities on a signal (momentum, value, quality, etc.).

### Steps
1. **Define the universe**: which securities, what filters (market cap, liquidity, sector)
2. **Define the signal**: computation, data requirements, any transformations
3. **Define portfolio construction**: quintile sorts, optimization, weighting scheme
4. **Define execution**: rebalancing frequency, execution assumption (close, next-open, VWAP)
5. **Define transaction costs**: spread model, market impact, any borrowing costs for shorts
6. **Split sample**: training (60%) and test (40%), or walk-forward
7. **Run backtest**: enforce point-in-time data, log all trades
8. **Compute metrics**: all standard metrics (see gqd-backtester agent)
9. **Run robustness checks**: parameter sensitivity, regime analysis, subsample stability
10. **Report**: with full methodology, not just results

### Common LLM Pitfalls
- Survivorship bias in universe construction (E003)
- Look-ahead in signal computation (E004)
- Unrealistic execution assumptions (closing price with no delay)
- Not reporting turnover and transaction costs (E013)

---

## Protocol: Time Series Strategy Backtest

### When to Use
Testing strategies that trade a single asset or small number of assets based on time-series signals (trend-following, mean-reversion, regime-switching).

### Steps
1. **Define the asset(s)**: what is being traded, data source
2. **Define the signal**: moving averages, momentum, volatility breakout, etc.
3. **Define position sizing**: fixed notional, volatility-targeting, Kelly criterion
4. **Define execution**: market orders, limit orders, timing within day
5. **Split sample**: training and test periods, ensure test period includes different regimes
6. **Run backtest**: step through each bar chronologically, no peeking ahead
7. **Compute metrics**: see standard list
8. **Test for data snooping**: if parameters were optimized, apply White's Reality Check or Hansen's SPA test
9. **Report regime-conditional performance**: separately for bull, bear, crisis, low-vol periods

### Common LLM Pitfalls
- Using close-to-close returns but executing at the close (need next-bar execution)
- Not accounting for overnight gaps in intraday strategies
- Volatility targeting using future volatility (must use backward-looking estimate)
- Ignoring margin/leverage constraints

---

## Protocol: Walk-Forward Optimization

### When to Use
When strategy has tunable parameters and you want to avoid in-sample overfitting.

### Steps
1. **Define parameter grid**: reasonable ranges for each parameter
2. **Define optimization criterion**: Sharpe, Calmar, or other risk-adjusted metric
3. **Define windows**: training window length, test window length, step size
4. **For each step**:
   a. Optimize on training window
   b. Apply best parameters to test window
   c. Record out-of-sample performance
5. **Concatenate** all out-of-sample periods for overall performance
6. **Compare**: walk-forward OOS vs full-sample optimized performance
7. **Report degradation ratio**: OOS Sharpe / In-sample Sharpe

### Common LLM Pitfalls
- Training window too short (overfitting to recent regime)
- Training window too long (stale parameters)
- Testing on data that was part of any training window (data leakage)
- Not reporting the number of parameter combinations tested

---

## Protocol: Statistical Significance Testing for Strategies

### When to Use
Determining whether a strategy's performance is statistically significant.

### Steps
1. **State the null hypothesis**: typically H0: mean excess return = 0
2. **Compute t-statistic**: t = mean(R_excess) / (std(R_excess) / sqrt(N))
3. **Account for autocorrelation**: if returns are autocorrelated, use Newey-West standard errors
4. **For Sharpe ratio**: compute confidence interval (Lo, 2002): SE(SR) ~ sqrt((1 + 0.5*SR^2) / N) for iid returns
5. **For multiple strategies**: apply Bonferroni correction (p_adj = p * M) or BH procedure
6. **For optimized strategies**: apply White's Reality Check or Hansen's SPA test
7. **Report**: t-stat, p-value, confidence interval, correction method, number of tests

### Common LLM Pitfalls
- Ignoring autocorrelation in returns (biases t-stat upward)
- Not correcting for multiple testing (E005)
- Confusing statistical and economic significance
- Using parametric tests when return distribution is non-normal
