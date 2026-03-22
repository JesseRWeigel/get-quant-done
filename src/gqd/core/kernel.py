"""Content-addressed verification kernel.

Runs predicates over evidence registries and produces SHA-256 verdicts.
Adapted from GPD's kernel.py for quantitative finance verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from .constants import VERIFICATION_CHECKS, SEVERITY_CRITICAL, SEVERITY_MAJOR, SEVERITY_MINOR, SEVERITY_NOTE


class Severity(str, Enum):
    CRITICAL = SEVERITY_CRITICAL
    MAJOR = SEVERITY_MAJOR
    MINOR = SEVERITY_MINOR
    NOTE = SEVERITY_NOTE


@dataclass
class CheckResult:
    """Result of a single verification check."""

    check_id: str
    name: str
    status: str  # PASS | FAIL | SKIP | WARN
    severity: Severity
    message: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    """Complete verification verdict with content-addressed hashes."""

    registry_hash: str
    predicates_hash: str
    verdict_hash: str
    overall: str  # PASS | FAIL | PARTIAL
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    results: dict[str, CheckResult] = field(default_factory=dict)
    summary: str = ""

    @property
    def critical_failures(self) -> list[CheckResult]:
        return [
            r
            for r in self.results.values()
            if r.status == "FAIL" and r.severity == Severity.CRITICAL
        ]

    @property
    def major_failures(self) -> list[CheckResult]:
        return [
            r
            for r in self.results.values()
            if r.status == "FAIL" and r.severity == Severity.MAJOR
        ]

    @property
    def all_failures(self) -> list[CheckResult]:
        return [r for r in self.results.values() if r.status == "FAIL"]

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == "PASS")

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == "FAIL")

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_hash": self.registry_hash,
            "predicates_hash": self.predicates_hash,
            "verdict_hash": self.verdict_hash,
            "overall": self.overall,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "results": {
                k: {
                    "check_id": v.check_id,
                    "name": v.name,
                    "status": v.status,
                    "severity": v.severity.value,
                    "message": v.message,
                    "evidence": v.evidence,
                    "suggestions": v.suggestions,
                }
                for k, v in self.results.items()
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# -- Predicate Type -----------------------------------------------------------

# A predicate takes an evidence registry and returns a CheckResult
Predicate = Callable[[dict[str, Any]], CheckResult]


# -- Built-in Financial Predicates -------------------------------------------

def check_no_arbitrage(evidence: dict[str, Any]) -> CheckResult:
    """Check that pricing models satisfy no-arbitrage conditions."""
    arbitrage_violations = evidence.get("arbitrage_violations", [])
    model_type = evidence.get("pricing_model", "unknown")

    if not evidence.get("no_arbitrage_checked", False):
        return CheckResult(
            check_id="no_arbitrage",
            name="No-Arbitrage",
            status="SKIP",
            severity=Severity.CRITICAL,
            message="No-arbitrage conditions not checked.",
            suggestions=[
                "Verify risk-neutral pricing measure exists.",
                "Check that model prices satisfy no-arbitrage bounds.",
                "For options: verify no calendar arbitrage and no butterfly arbitrage.",
            ],
        )

    if arbitrage_violations:
        return CheckResult(
            check_id="no_arbitrage",
            name="No-Arbitrage",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"Found {len(arbitrage_violations)} arbitrage violation(s) in {model_type} model.",
            evidence={"violations": arbitrage_violations},
            suggestions=[
                f"Address violation: {v}" for v in arbitrage_violations[:5]
            ],
        )

    return CheckResult(
        check_id="no_arbitrage",
        name="No-Arbitrage",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"No-arbitrage conditions verified for {model_type} model.",
    )


def check_put_call_parity(evidence: dict[str, Any]) -> CheckResult:
    """Check that option prices satisfy put-call parity."""
    parity_errors = evidence.get("put_call_parity_errors", [])
    max_error = evidence.get("put_call_parity_max_error", None)
    tolerance = evidence.get("put_call_parity_tolerance", 0.01)

    if not evidence.get("put_call_parity_checked", False):
        return CheckResult(
            check_id="put_call_parity",
            name="Put-Call Parity",
            status="SKIP",
            severity=Severity.CRITICAL,
            message="Put-call parity not checked (may not apply to this model).",
        )

    if parity_errors:
        return CheckResult(
            check_id="put_call_parity",
            name="Put-Call Parity",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"Put-call parity violated: max error {max_error}, tolerance {tolerance}.",
            evidence={"errors": parity_errors, "max_error": max_error},
            suggestions=["Check dividend handling.", "Verify interest rate convention."],
        )

    return CheckResult(
        check_id="put_call_parity",
        name="Put-Call Parity",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"Put-call parity holds within tolerance ({tolerance}).",
    )


def check_greeks_consistency(evidence: dict[str, Any]) -> CheckResult:
    """Check that numerical Greeks match analytical where available."""
    greeks_mismatches = evidence.get("greeks_mismatches", [])
    greeks_checked = evidence.get("greeks_checked", [])

    if not greeks_checked:
        return CheckResult(
            check_id="greeks_consistency",
            name="Greeks Consistency",
            status="SKIP",
            severity=Severity.MAJOR,
            message="No Greeks consistency checks performed.",
            suggestions=[
                "Compare numerical (finite-difference) Greeks with analytical formulas.",
                "Check delta-gamma-theta relationship (Black-Scholes PDE).",
            ],
        )

    if greeks_mismatches:
        return CheckResult(
            check_id="greeks_consistency",
            name="Greeks Consistency",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(greeks_mismatches)} Greek(s) inconsistent between numerical and analytical.",
            evidence={"mismatches": greeks_mismatches},
        )

    return CheckResult(
        check_id="greeks_consistency",
        name="Greeks Consistency",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"All {len(greeks_checked)} Greeks consistent.",
    )


def check_boundary_conditions(evidence: dict[str, Any]) -> CheckResult:
    """Check model satisfies known boundary conditions."""
    boundary_violations = evidence.get("boundary_violations", [])
    boundaries_checked = evidence.get("boundaries_checked", [])

    if not boundaries_checked:
        return CheckResult(
            check_id="boundary_conditions",
            name="Boundary Conditions",
            status="WARN",
            severity=Severity.MAJOR,
            message="No boundary conditions checked.",
            suggestions=[
                "Check deep ITM/OTM limits.",
                "Check behavior at expiry (payoff convergence).",
                "Check zero volatility and infinite volatility limits.",
                "Check behavior as time to expiry approaches zero and infinity.",
            ],
        )

    if boundary_violations:
        return CheckResult(
            check_id="boundary_conditions",
            name="Boundary Conditions",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(boundary_violations)} boundary condition(s) violated.",
            evidence={"violations": boundary_violations},
        )

    return CheckResult(
        check_id="boundary_conditions",
        name="Boundary Conditions",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"All {len(boundaries_checked)} boundary conditions satisfied.",
    )


def check_distribution_validity(evidence: dict[str, Any]) -> CheckResult:
    """Check that assumed distributions are consistent with data."""
    distribution_tests = evidence.get("distribution_tests", [])
    distribution_failures = evidence.get("distribution_failures", [])

    if not distribution_tests:
        return CheckResult(
            check_id="distribution_validity",
            name="Distribution Validity",
            status="WARN",
            severity=Severity.MAJOR,
            message="No distribution validity tests performed.",
            suggestions=[
                "Run Kolmogorov-Smirnov or Anderson-Darling tests.",
                "Check for fat tails, skewness, and autocorrelation.",
                "Compare assumed distribution with empirical distribution of returns.",
            ],
        )

    if distribution_failures:
        return CheckResult(
            check_id="distribution_validity",
            name="Distribution Validity",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(distribution_failures)} distribution assumption(s) rejected by data.",
            evidence={"failures": distribution_failures},
            suggestions=["Consider alternative distributions (Student-t, GEV, mixture models)."],
        )

    return CheckResult(
        check_id="distribution_validity",
        name="Distribution Validity",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"All {len(distribution_tests)} distribution assumptions consistent with data.",
    )


def check_backtest_integrity(evidence: dict[str, Any]) -> CheckResult:
    """Check for look-ahead bias, survivorship bias, and data snooping."""
    integrity_violations = evidence.get("backtest_integrity_violations", [])
    look_ahead_check = evidence.get("look_ahead_bias_checked", False)
    survivorship_check = evidence.get("survivorship_bias_checked", False)
    data_snooping_check = evidence.get("data_snooping_checked", False)

    if not evidence.get("backtest_conducted", False):
        return CheckResult(
            check_id="backtest_integrity",
            name="Backtest Integrity",
            status="SKIP",
            severity=Severity.CRITICAL,
            message="No backtest conducted (may not apply).",
        )

    unchecked = []
    if not look_ahead_check:
        unchecked.append("look-ahead bias")
    if not survivorship_check:
        unchecked.append("survivorship bias")
    if not data_snooping_check:
        unchecked.append("data snooping")

    if unchecked:
        return CheckResult(
            check_id="backtest_integrity",
            name="Backtest Integrity",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"Backtest integrity incomplete: {', '.join(unchecked)} not checked.",
            suggestions=[f"Verify no {bias} in backtest." for bias in unchecked],
        )

    if integrity_violations:
        return CheckResult(
            check_id="backtest_integrity",
            name="Backtest Integrity",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"Found {len(integrity_violations)} backtest integrity violation(s).",
            evidence={"violations": integrity_violations},
        )

    return CheckResult(
        check_id="backtest_integrity",
        name="Backtest Integrity",
        status="PASS",
        severity=Severity.CRITICAL,
        message="Backtest integrity verified: no look-ahead, survivorship, or data snooping bias.",
    )


def check_oos_performance(evidence: dict[str, Any]) -> CheckResult:
    """Check that results hold outside the training period."""
    oos_results = evidence.get("oos_results", {})
    is_results = evidence.get("in_sample_results", {})

    if not evidence.get("oos_tested", False):
        return CheckResult(
            check_id="oos_performance",
            name="Out-of-Sample Performance",
            status="WARN",
            severity=Severity.MAJOR,
            message="No out-of-sample testing performed.",
            suggestions=[
                "Split data into training and test periods.",
                "Use walk-forward analysis or expanding window.",
                "Report both in-sample and out-of-sample metrics.",
            ],
        )

    degradation = evidence.get("oos_degradation_pct", None)
    if degradation is not None and degradation > 50:
        return CheckResult(
            check_id="oos_performance",
            name="Out-of-Sample Performance",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"Severe OOS degradation: {degradation:.1f}% performance loss.",
            evidence={"oos_results": oos_results, "is_results": is_results},
            suggestions=["Likely overfitting. Simplify model or add regularization."],
        )

    return CheckResult(
        check_id="oos_performance",
        name="Out-of-Sample Performance",
        status="PASS",
        severity=Severity.MAJOR,
        message="Out-of-sample results consistent with in-sample.",
        evidence={"oos_results": oos_results},
    )


def check_risk_measure_coherence(evidence: dict[str, Any]) -> CheckResult:
    """Check risk measures satisfy coherence axioms (Artzner et al.)."""
    coherence_violations = evidence.get("coherence_violations", [])
    risk_measure = evidence.get("risk_measure_type", "unknown")

    if not evidence.get("coherence_checked", False):
        return CheckResult(
            check_id="risk_measure_coherence",
            name="Risk Measure Coherence",
            status="SKIP",
            severity=Severity.MAJOR,
            message="Risk measure coherence not checked.",
            suggestions=[
                "Check subadditivity: rho(X+Y) <= rho(X) + rho(Y).",
                "Check monotonicity: X <= Y => rho(X) <= rho(Y).",
                "Check translation invariance: rho(X+c) = rho(X) - c.",
                "Check positive homogeneity: rho(lambda*X) = lambda*rho(X).",
                "Note: VaR is NOT coherent (fails subadditivity). ES is coherent.",
            ],
        )

    if coherence_violations:
        return CheckResult(
            check_id="risk_measure_coherence",
            name="Risk Measure Coherence",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"Risk measure '{risk_measure}' violates {len(coherence_violations)} coherence axiom(s).",
            evidence={"violations": coherence_violations},
        )

    return CheckResult(
        check_id="risk_measure_coherence",
        name="Risk Measure Coherence",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"Risk measure '{risk_measure}' satisfies all checked coherence axioms.",
    )


def check_conservation_laws(evidence: dict[str, Any]) -> CheckResult:
    """Check portfolio value conservation and P&L attribution completeness."""
    conservation_errors = evidence.get("conservation_errors", [])

    if not evidence.get("conservation_checked", False):
        return CheckResult(
            check_id="conservation_laws",
            name="Conservation Laws",
            status="WARN",
            severity=Severity.MAJOR,
            message="Conservation / P&L attribution not checked.",
            suggestions=[
                "Verify portfolio value = sum of position values.",
                "Verify P&L attribution: total P&L = sum of component P&L.",
                "Check that cash flows balance (dividends, financing, transaction costs).",
            ],
        )

    if conservation_errors:
        return CheckResult(
            check_id="conservation_laws",
            name="Conservation Laws",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"Found {len(conservation_errors)} conservation / P&L attribution error(s).",
            evidence={"errors": conservation_errors},
        )

    return CheckResult(
        check_id="conservation_laws",
        name="Conservation Laws",
        status="PASS",
        severity=Severity.MAJOR,
        message="Portfolio value and P&L attribution verified.",
    )


def check_statistical_significance(evidence: dict[str, Any]) -> CheckResult:
    """Check statistical significance of results."""
    significance_issues = evidence.get("significance_issues", [])
    p_values = evidence.get("p_values", {})
    multiple_testing_corrected = evidence.get("multiple_testing_corrected", False)
    num_tests = evidence.get("num_hypothesis_tests", 0)

    if not evidence.get("significance_tested", False):
        return CheckResult(
            check_id="statistical_significance",
            name="Statistical Significance",
            status="WARN",
            severity=Severity.MAJOR,
            message="No statistical significance tests performed.",
            suggestions=[
                "Report t-statistics and p-values for key results.",
                "Compute confidence intervals for Sharpe ratios.",
                "Apply Bonferroni or BH correction if testing multiple hypotheses.",
            ],
        )

    if num_tests > 1 and not multiple_testing_corrected:
        return CheckResult(
            check_id="statistical_significance",
            name="Statistical Significance",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{num_tests} hypothesis tests without multiple testing correction.",
            evidence={"p_values": p_values},
            suggestions=["Apply Bonferroni, Holm, or Benjamini-Hochberg correction."],
        )

    if significance_issues:
        return CheckResult(
            check_id="statistical_significance",
            name="Statistical Significance",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(significance_issues)} statistical significance issue(s).",
            evidence={"issues": significance_issues, "p_values": p_values},
        )

    return CheckResult(
        check_id="statistical_significance",
        name="Statistical Significance",
        status="PASS",
        severity=Severity.MAJOR,
        message="Results are statistically significant with proper corrections.",
    )


def check_literature_comparison(evidence: dict[str, Any]) -> CheckResult:
    """Check results compared against published benchmarks."""
    comparisons = evidence.get("literature_comparisons", [])
    discrepancies = evidence.get("literature_discrepancies", [])

    if not comparisons:
        return CheckResult(
            check_id="literature_comparison",
            name="Literature Comparison",
            status="WARN",
            severity=Severity.MINOR,
            message="No literature comparison performed.",
            suggestions=[
                "Compare model prices with published benchmarks.",
                "Compare strategy performance with known factor returns.",
                "Compare risk estimates with industry standards.",
            ],
        )

    if discrepancies:
        return CheckResult(
            check_id="literature_comparison",
            name="Literature Comparison",
            status="FAIL",
            severity=Severity.MINOR,
            message=f"Results disagree with {len(discrepancies)} published benchmark(s).",
            evidence={"discrepancies": discrepancies},
        )

    return CheckResult(
        check_id="literature_comparison",
        name="Literature Comparison",
        status="PASS",
        severity=Severity.MINOR,
        message=f"Consistent with {len(comparisons)} published benchmark(s).",
    )


def check_robustness(evidence: dict[str, Any]) -> CheckResult:
    """Check sensitivity to parameter choices, data windows, and market regimes."""
    robustness_failures = evidence.get("robustness_failures", [])
    robustness_tests = evidence.get("robustness_tests", [])

    if not robustness_tests:
        return CheckResult(
            check_id="robustness",
            name="Robustness",
            status="WARN",
            severity=Severity.MINOR,
            message="No robustness tests performed.",
            suggestions=[
                "Test sensitivity to key parameters (e.g., lookback window, threshold).",
                "Test across market regimes (bull, bear, sideways, crisis).",
                "Test with different data windows and frequencies.",
                "Test with perturbed transaction costs.",
            ],
        )

    if robustness_failures:
        return CheckResult(
            check_id="robustness",
            name="Robustness",
            status="FAIL",
            severity=Severity.MINOR,
            message=f"Results not robust: {len(robustness_failures)} sensitivity test(s) failed.",
            evidence={"failures": robustness_failures},
        )

    return CheckResult(
        check_id="robustness",
        name="Robustness",
        status="PASS",
        severity=Severity.MINOR,
        message=f"Results robust across {len(robustness_tests)} sensitivity tests.",
    )


# -- Default predicate registry -----------------------------------------------

DEFAULT_PREDICATES: dict[str, Predicate] = {
    "no_arbitrage": check_no_arbitrage,
    "put_call_parity": check_put_call_parity,
    "greeks_consistency": check_greeks_consistency,
    "boundary_conditions": check_boundary_conditions,
    "distribution_validity": check_distribution_validity,
    "backtest_integrity": check_backtest_integrity,
    "oos_performance": check_oos_performance,
    "risk_measure_coherence": check_risk_measure_coherence,
    "conservation_laws": check_conservation_laws,
    "statistical_significance": check_statistical_significance,
    "literature_comparison": check_literature_comparison,
    "robustness": check_robustness,
}


# -- Verification Kernel ------------------------------------------------------

class VerificationKernel:
    """Content-addressed verification kernel.

    Runs predicates over evidence registries and produces
    SHA-256 verdicts for reproducibility and tamper-evidence.
    """

    def __init__(self, predicates: dict[str, Predicate] | None = None):
        self.predicates = predicates or dict(DEFAULT_PREDICATES)

    def _hash(self, data: str) -> str:
        return f"sha256:{hashlib.sha256(data.encode()).hexdigest()}"

    def verify(self, evidence: dict[str, Any]) -> Verdict:
        """Run all predicates against evidence and produce a verdict."""
        # Hash inputs
        evidence_json = json.dumps(evidence, sort_keys=True, default=str)
        registry_hash = self._hash(evidence_json)

        predicate_names = json.dumps(sorted(self.predicates.keys()))
        predicates_hash = self._hash(predicate_names)

        # Run predicates
        results: dict[str, CheckResult] = {}
        for check_id, predicate in self.predicates.items():
            try:
                result = predicate(evidence)
                results[check_id] = result
            except Exception as e:
                results[check_id] = CheckResult(
                    check_id=check_id,
                    name=check_id.replace("_", " ").title(),
                    status="FAIL",
                    severity=Severity.MAJOR,
                    message=f"Predicate raised exception: {e}",
                )

        # Determine overall status
        has_critical_fail = any(
            r.status == "FAIL" and r.severity == Severity.CRITICAL
            for r in results.values()
        )
        has_major_fail = any(
            r.status == "FAIL" and r.severity == Severity.MAJOR
            for r in results.values()
        )

        if has_critical_fail:
            overall = "FAIL"
        elif has_major_fail:
            overall = "PARTIAL"
        else:
            overall = "PASS"

        # Hash the results for tamper-evidence
        results_json = json.dumps(
            {k: v.message for k, v in results.items()},
            sort_keys=True,
        )
        verdict_hash = self._hash(
            f"{registry_hash}:{predicates_hash}:{results_json}"
        )

        # Build summary
        pass_count = sum(1 for r in results.values() if r.status == "PASS")
        fail_count = sum(1 for r in results.values() if r.status == "FAIL")
        skip_count = sum(1 for r in results.values() if r.status == "SKIP")
        warn_count = sum(1 for r in results.values() if r.status == "WARN")

        summary = (
            f"{overall}: {pass_count} passed, {fail_count} failed, "
            f"{warn_count} warnings, {skip_count} skipped "
            f"out of {len(results)} checks."
        )

        return Verdict(
            registry_hash=registry_hash,
            predicates_hash=predicates_hash,
            verdict_hash=verdict_hash,
            overall=overall,
            results=results,
            summary=summary,
        )
