"""Configuration — model tiers, autonomy modes, research modes.

Adapted from GPD's config.py for quantitative finance research.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import (
    AUTONOMY_BALANCED,
    RESEARCH_BALANCED,
    TIER_1,
    TIER_2,
    TIER_3,
    VALID_AUTONOMY_MODES,
    VALID_RESEARCH_MODES,
    ProjectLayout,
)


# -- Model Profiles -----------------------------------------------------------
# Each profile maps agent roles to model tiers.

MODEL_PROFILES: dict[str, dict[str, str]] = {
    "pricing-theory": {
        "planner": TIER_1,
        "executor": TIER_1,
        "verifier": TIER_1,
        "researcher": TIER_2,
        "backtester": TIER_2,
        "paper_writer": TIER_1,
        "referee": TIER_1,
    },
    "empirical": {
        "planner": TIER_2,
        "executor": TIER_1,
        "verifier": TIER_1,
        "researcher": TIER_2,
        "backtester": TIER_1,
        "paper_writer": TIER_2,
        "referee": TIER_2,
    },
    "exploratory": {
        "planner": TIER_2,
        "executor": TIER_2,
        "verifier": TIER_2,
        "researcher": TIER_1,
        "backtester": TIER_2,
        "paper_writer": TIER_3,
        "referee": TIER_2,
    },
    "backtesting": {
        "planner": TIER_2,
        "executor": TIER_2,
        "verifier": TIER_1,
        "researcher": TIER_3,
        "backtester": TIER_1,
        "paper_writer": TIER_3,
        "referee": TIER_2,
    },
    "paper-writing": {
        "planner": TIER_3,
        "executor": TIER_3,
        "verifier": TIER_2,
        "researcher": TIER_2,
        "backtester": TIER_3,
        "paper_writer": TIER_1,
        "referee": TIER_1,
    },
}

# -- Research Mode Parameters -------------------------------------------------

RESEARCH_MODE_PARAMS: dict[str, dict[str, Any]] = {
    "explore": {
        "candidate_approaches": 5,
        "literature_searches": (15, 25),
        "planning_style": "parallel",
        "description": "Maximum breadth — survey many models and strategies before committing.",
    },
    "balanced": {
        "candidate_approaches": 3,
        "literature_searches": (8, 12),
        "planning_style": "sequential",
        "description": "Standard depth — 2-3 model specifications, moderate literature search.",
    },
    "exploit": {
        "candidate_approaches": 1,
        "literature_searches": (3, 5),
        "planning_style": "focused",
        "description": "Narrow focus — confirm known methodology, minimal survey.",
    },
    "adaptive": {
        "candidate_approaches": 5,
        "literature_searches": (8, 25),
        "planning_style": "adaptive",
        "description": "Starts broad, transitions to narrow when evidence criteria met.",
        "transition_criteria": {
            "decisive_comparison_evidence": True,
            "min_convention_locks": 5,
            "no_recent_inconsistencies": True,
            "converging_evidence": True,
        },
    },
}


@dataclass
class GQDConfig:
    """Project configuration."""

    model_profile: str = "pricing-theory"
    model_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    autonomy: str = AUTONOMY_BALANCED
    research_mode: str = RESEARCH_BALANCED
    commit_docs: bool = True
    workflow: dict[str, Any] = field(default_factory=lambda: {
        "verify_between_waves": "auto",
        "max_plan_tasks": 10,
        "max_deviation_retries": 2,
        "context_budget_warning_pct": 80,
    })

    def get_tier_for_role(self, role: str) -> str:
        """Get the model tier for an agent role."""
        profile = MODEL_PROFILES.get(self.model_profile, MODEL_PROFILES["pricing-theory"])
        return profile.get(role, TIER_2)

    def get_research_params(self) -> dict[str, Any]:
        """Get parameters for current research mode."""
        return RESEARCH_MODE_PARAMS.get(
            self.research_mode,
            RESEARCH_MODE_PARAMS["balanced"],
        )

    @classmethod
    def load(cls, layout: ProjectLayout) -> "GQDConfig":
        """Load config from .gqd/config.json."""
        config_path = layout.config_json
        if config_path.exists():
            data = json.loads(config_path.read_text())
            return cls(**{
                k: v for k, v in data.items()
                if k in cls.__dataclass_fields__
            })
        return cls()

    def save(self, layout: ProjectLayout) -> None:
        """Save config to .gqd/config.json."""
        layout.gqd_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "model_profile": self.model_profile,
            "model_overrides": self.model_overrides,
            "autonomy": self.autonomy,
            "research_mode": self.research_mode,
            "commit_docs": self.commit_docs,
            "workflow": self.workflow,
        }
        layout.config_json.write_text(json.dumps(data, indent=2))

    def validate(self) -> list[str]:
        """Validate config. Returns list of error messages."""
        errors = []
        if self.model_profile not in MODEL_PROFILES:
            errors.append(
                f"Unknown model_profile: {self.model_profile}. "
                f"Valid: {list(MODEL_PROFILES.keys())}"
            )
        if self.autonomy not in VALID_AUTONOMY_MODES:
            errors.append(
                f"Unknown autonomy mode: {self.autonomy}. "
                f"Valid: {VALID_AUTONOMY_MODES}"
            )
        if self.research_mode not in VALID_RESEARCH_MODES:
            errors.append(
                f"Unknown research_mode: {self.research_mode}. "
                f"Valid: {VALID_RESEARCH_MODES}"
            )
        return errors
