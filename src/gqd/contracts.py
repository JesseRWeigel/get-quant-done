"""Research contracts — Pydantic models for claims, deliverables, and acceptance tests.

Adapted from GPD's contracts.py for quantitative finance research.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class Claim(BaseModel):
    """A quantitative finance claim to be proved or validated."""

    id: str
    statement: str
    claim_type: str = "proposition"  # proposition | theorem | empirical | model_property | strategy_property
    assumptions: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)  # Other claim IDs
    status: str = "unvalidated"  # unvalidated | validated | refuted | partial


class Deliverable(BaseModel):
    """An expected output artifact from a phase/plan."""

    id: str
    description: str
    artifact_type: str  # derivation | implementation | backtest | figure | table | manuscript_section | data
    file_path: str = ""
    acceptance_tests: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending | delivered | verified | rejected


class AcceptanceTest(BaseModel):
    """A concrete test for a deliverable."""

    id: str
    description: str
    test_type: str  # existence | content | verification | consistency | statistical | backtest
    predicate: str = ""  # Human-readable predicate
    status: str = "pending"  # pending | passed | failed


class ForbiddenProxy(BaseModel):
    """Something that must NOT be used as evidence of completion.

    Prevents agents from claiming success based on superficial signals.
    """

    description: str
    reason: str


class ResearchContract(BaseModel):
    """A complete research contract for a phase or plan.

    Defines what must be achieved, how to verify it, and what NOT to accept.
    """

    phase_id: str
    plan_id: str = ""
    goal: str

    claims: list[Claim] = Field(default_factory=list)
    deliverables: list[Deliverable] = Field(default_factory=list)
    acceptance_tests: list[AcceptanceTest] = Field(default_factory=list)

    forbidden_proxies: list[ForbiddenProxy] = Field(
        default_factory=lambda: [
            ForbiddenProxy(
                description="Agent stating 'model is correct' without derivation",
                reason="Full derivation must exist on disk and pass verification.",
            ),
            ForbiddenProxy(
                description="Backtest results without out-of-sample validation",
                reason="In-sample performance alone is not evidence of strategy validity.",
            ),
            ForbiddenProxy(
                description="Pricing formula without no-arbitrage verification",
                reason="All pricing models must satisfy no-arbitrage conditions.",
            ),
            ForbiddenProxy(
                description="Strategy Sharpe ratio without statistical significance test",
                reason="Performance metrics must include confidence intervals and p-values.",
            ),
            ForbiddenProxy(
                description="Backtest without survivorship bias and look-ahead bias checks",
                reason="Backtest integrity must be explicitly verified.",
            ),
        ]
    )

    def all_claims_resolved(self) -> bool:
        return all(c.status in ("validated", "refuted") for c in self.claims)

    def all_deliverables_verified(self) -> bool:
        return all(d.status == "verified" for d in self.deliverables)

    def all_tests_passed(self) -> bool:
        return all(t.status == "passed" for t in self.acceptance_tests)


class AgentReturn(BaseModel):
    """Structured return envelope from subagents.

    Every subagent MUST produce this in their SUMMARY.md.
    The orchestrator uses this — not prose — to determine success.
    """

    status: str  # completed | checkpoint | blocked | failed
    files_written: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    claims_validated: list[str] = Field(default_factory=list)  # Claim IDs
    conventions_proposed: dict[str, str] = Field(default_factory=dict)
    verification_evidence: dict[str, Any] = Field(default_factory=dict)
