"""Single source of truth for all directory/file names and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# -- Environment Variables ----------------------------------------------------

ENV_GQD_HOME = "GQD_HOME"
ENV_GQD_PROJECT = "GQD_PROJECT"
ENV_GQD_INSTALL_DIR = "GQD_INSTALL_DIR"
ENV_GQD_DEBUG = "GQD_DEBUG"
ENV_GQD_AUTONOMY = "GQD_AUTONOMY"

# -- File Names ---------------------------------------------------------------

STATE_MD = "STATE.md"
STATE_JSON = "state.json"
STATE_WRITE_INTENT = ".state-write-intent"
ROADMAP_MD = "ROADMAP.md"
CONFIG_JSON = "config.json"
CONVENTIONS_JSON = "conventions.json"

PLAN_PREFIX = "PLAN"
SUMMARY_PREFIX = "SUMMARY"
RESEARCH_MD = "RESEARCH.md"
RESEARCH_DIGEST_MD = "RESEARCH-DIGEST.md"
CONTINUE_HERE_MD = ".continue-here.md"

# -- Directory Names ----------------------------------------------------------

GQD_DIR = ".gqd"
OBSERVABILITY_DIR = "observability"
SESSIONS_DIR = "sessions"
TRACES_DIR = "traces"
KNOWLEDGE_DIR = "knowledge"
PAPER_DIR = "paper"
SCRATCH_DIR = ".scratch"
DATA_DIR = "data"
BACKTEST_DIR = "backtests"

# -- Git ----------------------------------------------------------------------

CHECKPOINT_TAG_PREFIX = "gqd-checkpoint"
COMMIT_PREFIX = "[gqd]"

# -- Autonomy Modes -----------------------------------------------------------

AUTONOMY_SUPERVISED = "supervised"
AUTONOMY_BALANCED = "balanced"
AUTONOMY_YOLO = "yolo"
VALID_AUTONOMY_MODES = {AUTONOMY_SUPERVISED, AUTONOMY_BALANCED, AUTONOMY_YOLO}

# -- Research Modes -----------------------------------------------------------

RESEARCH_EXPLORE = "explore"
RESEARCH_BALANCED = "balanced"
RESEARCH_EXPLOIT = "exploit"
RESEARCH_ADAPTIVE = "adaptive"
VALID_RESEARCH_MODES = {RESEARCH_EXPLORE, RESEARCH_BALANCED, RESEARCH_EXPLOIT, RESEARCH_ADAPTIVE}

# -- Model Tiers --------------------------------------------------------------

TIER_1 = "tier-1"  # Highest capability
TIER_2 = "tier-2"  # Balanced
TIER_3 = "tier-3"  # Fastest

# -- Verification Severity ----------------------------------------------------

SEVERITY_CRITICAL = "CRITICAL"  # Blocks all downstream work
SEVERITY_MAJOR = "MAJOR"        # Must resolve before conclusions
SEVERITY_MINOR = "MINOR"        # Must resolve before publication
SEVERITY_NOTE = "NOTE"          # Informational

# -- Convention Lock Fields (Quantitative Finance) ----------------------------

CONVENTION_FIELDS = [
    "pricing_model",              # Black-Scholes, Heston, SABR, local vol, etc.
    "risk_free_rate",             # Continuously compounded, discrete, source (SOFR, Treasury)
    "day_count_convention",       # ACT/360, ACT/365, 30/360, ACT/ACT
    "distribution_assumptions",   # Normal, log-normal, Student-t, GEV, etc.
    "risk_measure",               # VaR confidence level, ES, spectral risk measures
    "return_convention",          # Simple returns, log returns, excess returns
    "benchmark_definition",       # S&P 500, risk-free, custom portfolio
    "transaction_cost_model",     # Fixed, proportional, market impact model
    "rebalancing_frequency",      # Daily, weekly, monthly, event-driven
    "data_source",                # Bloomberg, CRSP, Yahoo Finance, cleaning methodology
]

# -- Verification Checks (Financial Consistency) ------------------------------

VERIFICATION_CHECKS = [
    "no_arbitrage",               # Pricing models satisfy no-arbitrage conditions
    "put_call_parity",            # Option prices are internally consistent
    "greeks_consistency",         # Numerical Greeks match analytical where available
    "boundary_conditions",        # Model satisfies known limits (deep ITM/OTM, expiry)
    "distribution_validity",      # Assumed distributions consistent with data
    "backtest_integrity",         # No look-ahead bias, survivorship bias, data snooping
    "oos_performance",            # Results hold outside training period
    "risk_measure_coherence",     # Subadditivity, monotonicity, translation invariance, positive homogeneity
    "conservation_laws",          # Portfolio value, P&L attribution completeness
    "statistical_significance",   # t-stats, Sharpe CIs, multiple testing corrections
    "literature_comparison",      # Results compared with published benchmarks
    "robustness",                 # Sensitivity to parameters, data windows, market regimes
]


@dataclass(frozen=True)
class ProjectLayout:
    """Resolved paths for a GQD project."""

    root: Path

    @property
    def gqd_dir(self) -> Path:
        return self.root / GQD_DIR

    @property
    def state_md(self) -> Path:
        return self.gqd_dir / STATE_MD

    @property
    def state_json(self) -> Path:
        return self.gqd_dir / STATE_JSON

    @property
    def state_write_intent(self) -> Path:
        return self.gqd_dir / STATE_WRITE_INTENT

    @property
    def roadmap_md(self) -> Path:
        return self.gqd_dir / ROADMAP_MD

    @property
    def config_json(self) -> Path:
        return self.gqd_dir / CONFIG_JSON

    @property
    def conventions_json(self) -> Path:
        return self.gqd_dir / CONVENTIONS_JSON

    @property
    def observability_dir(self) -> Path:
        return self.gqd_dir / OBSERVABILITY_DIR

    @property
    def sessions_dir(self) -> Path:
        return self.observability_dir / SESSIONS_DIR

    @property
    def traces_dir(self) -> Path:
        return self.gqd_dir / TRACES_DIR

    @property
    def knowledge_dir(self) -> Path:
        return self.root / KNOWLEDGE_DIR

    @property
    def paper_dir(self) -> Path:
        return self.root / PAPER_DIR

    @property
    def scratch_dir(self) -> Path:
        return self.root / SCRATCH_DIR

    @property
    def data_dir(self) -> Path:
        return self.root / DATA_DIR

    @property
    def backtest_dir(self) -> Path:
        return self.root / BACKTEST_DIR

    @property
    def continue_here(self) -> Path:
        return self.gqd_dir / CONTINUE_HERE_MD

    def phase_dir(self, phase: str) -> Path:
        return self.root / f"phase-{phase}"

    def plan_path(self, phase: str, plan_number: str) -> Path:
        return self.phase_dir(phase) / f"{PLAN_PREFIX}-{plan_number}.md"

    def summary_path(self, phase: str, plan_number: str) -> Path:
        return self.phase_dir(phase) / f"{SUMMARY_PREFIX}-{plan_number}.md"

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        for d in [
            self.gqd_dir,
            self.observability_dir,
            self.sessions_dir,
            self.traces_dir,
            self.knowledge_dir,
            self.scratch_dir,
            self.data_dir,
            self.backtest_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) looking for .gqd/ directory."""
    current = start or Path.cwd()
    while current != current.parent:
        if (current / GQD_DIR).is_dir():
            return current
        current = current.parent
    raise FileNotFoundError(
        f"No {GQD_DIR}/ directory found. Run 'gqd init' to create a project."
    )


def get_layout(start: Path | None = None) -> ProjectLayout:
    """Get the project layout, finding the root automatically."""
    env_project = os.environ.get(ENV_GQD_PROJECT)
    if env_project:
        return ProjectLayout(root=Path(env_project))
    return ProjectLayout(root=find_project_root(start))
