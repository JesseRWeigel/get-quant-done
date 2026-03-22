"""Convention lock management for quantitative finance model assumptions.

Ensures model assumptions don't drift across phases of a research project.
Adapted from GPD's conventions.py for quantitative finance.
"""

from __future__ import annotations

from typing import Any

from .constants import CONVENTION_FIELDS
from .state import StateEngine, ConventionLock


# -- Convention Field Descriptions --------------------------------------------

CONVENTION_DESCRIPTIONS: dict[str, str] = {
    "pricing_model": (
        "The pricing model used for derivatives valuation. Examples: "
        "Black-Scholes (geometric Brownian motion), Heston (stochastic volatility), "
        "SABR (stochastic alpha-beta-rho), local volatility (Dupire), "
        "rough Bergomi, jump-diffusion (Merton), variance gamma."
    ),
    "risk_free_rate": (
        "The risk-free rate convention: continuously compounded vs discrete compounding, "
        "and the source. Examples: SOFR, Fed Funds, Treasury yields (which maturity), "
        "OIS rates. Also specifies whether rates are annualized and the compounding frequency."
    ),
    "day_count_convention": (
        "How days are counted for accrual calculations. Common conventions: "
        "ACT/360 (money markets), ACT/365 (bonds in UK/AUS), 30/360 (US corporate bonds), "
        "ACT/ACT (US Treasuries). Must be consistent across all instruments."
    ),
    "distribution_assumptions": (
        "The probability distribution assumed for asset returns or other random variables. "
        "Examples: normal (Gaussian), log-normal (for prices), Student-t (fat tails), "
        "generalized extreme value (GEV), normal inverse Gaussian (NIG), "
        "mixture of normals, empirical distribution."
    ),
    "risk_measure": (
        "The risk measure used and its parameters. Examples: "
        "VaR at 95% or 99% confidence (NOT coherent — fails subadditivity), "
        "Expected Shortfall (CVaR) at 97.5%, spectral risk measures, "
        "maximum drawdown, standard deviation."
    ),
    "return_convention": (
        "How returns are calculated: simple returns ((P1-P0)/P0), "
        "log returns (ln(P1/P0)), excess returns (R - Rf), "
        "or total returns (including dividends). Also: annualization method "
        "(multiply by sqrt(252) for daily to annual volatility)."
    ),
    "benchmark_definition": (
        "The benchmark portfolio or index for performance comparison. "
        "Examples: S&P 500 total return, risk-free rate, 60/40 stock/bond, "
        "equal-weight universe, custom factor portfolio. Must specify whether "
        "returns are gross or net of costs."
    ),
    "transaction_cost_model": (
        "How transaction costs are modeled. Examples: "
        "fixed per-trade cost, proportional (basis points), "
        "market impact model (square-root model, Almgren-Chriss), "
        "bid-ask spread based. Specify whether slippage is included."
    ),
    "rebalancing_frequency": (
        "How often the portfolio is rebalanced. Examples: "
        "daily, weekly (which day), monthly (which day), quarterly, "
        "event-driven (threshold-based). Also: how partial fills and "
        "execution timing are handled."
    ),
    "data_source": (
        "The data provider and cleaning methodology. Examples: "
        "CRSP (academic), Bloomberg (professional), Yahoo Finance (free), "
        "Refinitiv, WRDS. Must specify: survivorship bias handling, "
        "corporate action adjustments, handling of missing data, "
        "point-in-time vs revised data."
    ),
}

# -- Convention Validation ----------------------------------------------------

# Common valid values for quick validation
CONVENTION_EXAMPLES: dict[str, list[str]] = {
    "pricing_model": [
        "Black-Scholes (GBM, constant volatility)",
        "Heston (stochastic volatility, mean-reverting)",
        "SABR (alpha, beta, rho parameterization)",
        "Local volatility (Dupire)",
        "Rough Bergomi (H < 0.5)",
    ],
    "risk_free_rate": [
        "SOFR, continuously compounded, annualized",
        "3-month Treasury bill, discrete, annualized",
        "OIS rate, continuously compounded",
    ],
    "day_count_convention": [
        "ACT/360",
        "ACT/365",
        "30/360",
        "ACT/ACT (ISDA)",
    ],
    "distribution_assumptions": [
        "Log-normal (for prices), normal (for log-returns)",
        "Student-t with estimated degrees of freedom",
        "Normal inverse Gaussian (NIG)",
        "Empirical distribution (non-parametric)",
    ],
    "risk_measure": [
        "VaR 99%, 1-day horizon (Basel III)",
        "Expected Shortfall 97.5%, 1-day horizon",
        "Maximum drawdown over rolling 252-day window",
    ],
    "return_convention": [
        "Log returns, excess over risk-free, annualized",
        "Simple returns, gross of costs",
        "Total returns including dividends, net of costs",
    ],
}


def get_field_description(field: str) -> str:
    """Get the description for a convention field."""
    return CONVENTION_DESCRIPTIONS.get(field, f"Convention field: {field}")


def get_field_examples(field: str) -> list[str]:
    """Get example values for a convention field."""
    return CONVENTION_EXAMPLES.get(field, [])


def list_all_fields() -> list[dict[str, Any]]:
    """List all convention fields with descriptions and examples."""
    return [
        {
            "field": f,
            "description": get_field_description(f),
            "examples": get_field_examples(f),
        }
        for f in CONVENTION_FIELDS
    ]


def check_conventions(engine: StateEngine) -> dict[str, Any]:
    """Check which conventions are locked and which are missing.

    Returns a report dict with locked, unlocked, and coverage stats.
    """
    state = engine.load()
    locked = {}
    unlocked = []

    for field in CONVENTION_FIELDS:
        if field in state.conventions:
            locked[field] = {
                "value": state.conventions[field].value,
                "locked_by": state.conventions[field].locked_by,
                "rationale": state.conventions[field].rationale,
            }
        else:
            unlocked.append(field)

    return {
        "locked": locked,
        "unlocked": unlocked,
        "coverage": f"{len(locked)}/{len(CONVENTION_FIELDS)}",
        "coverage_pct": round(100 * len(locked) / len(CONVENTION_FIELDS), 1)
        if CONVENTION_FIELDS
        else 100.0,
    }


def diff_conventions(
    engine: StateEngine,
    proposed: dict[str, str],
) -> dict[str, Any]:
    """Compare proposed convention values against current locks.

    Returns conflicts, new fields, and matching fields.
    """
    state = engine.load()
    conflicts = {}
    new_fields = {}
    matching = {}

    for field, proposed_value in proposed.items():
        if field in state.conventions:
            current = state.conventions[field].value
            if current != proposed_value:
                conflicts[field] = {
                    "current": current,
                    "proposed": proposed_value,
                }
            else:
                matching[field] = current
        else:
            new_fields[field] = proposed_value

    return {
        "conflicts": conflicts,
        "new_fields": new_fields,
        "matching": matching,
        "has_conflicts": bool(conflicts),
    }
