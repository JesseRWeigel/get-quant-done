"""Dual-write state engine — STATE.md + state.json kept in sync.

Atomic writes with file locking and intent markers for crash recovery.
This is the authoritative store for project state.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .constants import ProjectLayout, get_layout


class PhaseState(BaseModel):
    """State of a single phase."""

    id: str
    title: str
    status: str = "pending"  # pending | active | completed | blocked
    current_plan: str | None = None
    plans_completed: list[str] = Field(default_factory=list)
    plans_total: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    verification_status: str | None = None  # None | passed | failed | partial


class ConventionLock(BaseModel):
    """A locked convention field."""

    field: str
    value: str
    locked_by: str  # Which phase/plan locked it
    locked_at: str
    rationale: str = ""


class DecisionLogEntry(BaseModel):
    """A recorded decision."""

    timestamp: str
    phase: str
    decision: str
    rationale: str
    agent: str = ""


class ProjectState(BaseModel):
    """Full project state."""

    project_name: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Current position
    current_milestone: str = "v1.0"
    current_phase: str = ""
    current_plan: str = ""

    # Phase tracking
    phases: dict[str, PhaseState] = Field(default_factory=dict)

    # Convention locks
    conventions: dict[str, ConventionLock] = Field(default_factory=dict)

    # Decision log
    decisions: list[DecisionLogEntry] = Field(default_factory=list)

    # Intermediate results (key-value store for cross-phase data)
    results: dict[str, Any] = Field(default_factory=dict)

    # Research mode
    research_mode: str = "balanced"
    autonomy_mode: str = "balanced"

    # Metrics
    total_tasks_completed: int = 0
    total_verification_passes: int = 0
    total_verification_failures: int = 0


class StateEngine:
    """Dual-write state engine with file locking and crash recovery."""

    def __init__(self, layout: ProjectLayout | None = None):
        self.layout = layout or get_layout()
        self._lock_fd: int | None = None

    def _acquire_lock(self) -> None:
        """Acquire file lock for atomic state operations."""
        lock_path = self.layout.gqd_dir / ".state.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_fd = open(lock_path, "w")
        fcntl.flock(self._lock_fd, fcntl.LOCK_EX)

    def _release_lock(self) -> None:
        """Release file lock."""
        if self._lock_fd:
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            self._lock_fd.close()
            self._lock_fd = None

    def _write_intent(self) -> None:
        """Write intent marker for crash recovery."""
        intent_path = self.layout.state_write_intent
        intent_path.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pid": __import__("os").getpid(),
                }
            )
        )

    def _clear_intent(self) -> None:
        """Clear intent marker after successful write."""
        intent_path = self.layout.state_write_intent
        if intent_path.exists():
            intent_path.unlink()

    def load(self) -> ProjectState:
        """Load state from state.json (authoritative source)."""
        json_path = self.layout.state_json
        if json_path.exists():
            data = json.loads(json_path.read_text())
            return ProjectState(**data)
        # Fall back to empty state
        return ProjectState()

    def save(self, state: ProjectState) -> None:
        """Atomic dual-write: state.json + STATE.md."""
        self._acquire_lock()
        try:
            self._write_intent()

            state.updated_at = datetime.now(timezone.utc).isoformat()

            # Write state.json (authoritative)
            self.layout.gqd_dir.mkdir(parents=True, exist_ok=True)
            json_data = state.model_dump(mode="json")
            self.layout.state_json.write_text(
                json.dumps(json_data, indent=2, default=str)
            )

            # Write STATE.md (human-readable)
            md_content = self._render_state_md(state)
            self.layout.state_md.write_text(md_content)

            self._clear_intent()
        finally:
            self._release_lock()

    def _render_state_md(self, state: ProjectState) -> str:
        """Render human-readable STATE.md from state object."""
        lines = [
            f"# {state.project_name or 'Untitled Project'} — State",
            "",
            f"**Milestone**: {state.current_milestone}",
            f"**Phase**: {state.current_phase or '(none)'}",
            f"**Plan**: {state.current_plan or '(none)'}",
            f"**Research Mode**: {state.research_mode}",
            f"**Autonomy**: {state.autonomy_mode}",
            f"**Updated**: {state.updated_at}",
            "",
        ]

        # Phases
        if state.phases:
            lines.append("## Phases")
            lines.append("")
            for pid, phase in state.phases.items():
                status_icon = {
                    "pending": "[ ]",
                    "active": "[~]",
                    "completed": "[x]",
                    "blocked": "[!]",
                }.get(phase.status, "[ ]")
                lines.append(
                    f"- {status_icon} **Phase {pid}**: {phase.title} "
                    f"({phase.status})"
                )
                if phase.plans_total > 0:
                    lines.append(
                        f"  - Plans: {len(phase.plans_completed)}/{phase.plans_total}"
                    )
                if phase.verification_status:
                    lines.append(
                        f"  - Verification: {phase.verification_status}"
                    )
            lines.append("")

        # Convention locks
        if state.conventions:
            lines.append("## Convention Locks")
            lines.append("")
            for field_name, lock in state.conventions.items():
                lines.append(f"- **{field_name}**: {lock.value}")
                if lock.rationale:
                    lines.append(f"  - Rationale: {lock.rationale}")
            lines.append("")

        # Recent decisions
        if state.decisions:
            lines.append("## Recent Decisions")
            lines.append("")
            for entry in state.decisions[-10:]:  # Last 10
                lines.append(
                    f"- [{entry.timestamp[:10]}] ({entry.phase}) {entry.decision}"
                )
            lines.append("")

        # Metrics
        lines.append("## Metrics")
        lines.append("")
        lines.append(f"- Tasks completed: {state.total_tasks_completed}")
        lines.append(f"- Verification passes: {state.total_verification_passes}")
        lines.append(f"- Verification failures: {state.total_verification_failures}")
        lines.append("")

        return "\n".join(lines)

    def recover_if_needed(self) -> bool:
        """Check for crash recovery — returns True if recovery was needed."""
        intent_path = self.layout.state_write_intent
        if not intent_path.exists():
            return False

        # Intent marker exists — previous write may have been interrupted
        json_path = self.layout.state_json
        md_path = self.layout.state_md

        if json_path.exists():
            # state.json exists — re-render STATE.md from it
            state = self.load()
            md_content = self._render_state_md(state)
            md_path.write_text(md_content)
            self._clear_intent()
            return True

        # Neither exists or only MD exists — clear intent, start fresh
        self._clear_intent()
        return False

    def sync(self) -> ProjectState:
        """Reconcile state.json and STATE.md — json is authoritative."""
        state = self.load()
        self.save(state)
        return state

    # -- Convenience Methods --------------------------------------------------

    def set_convention(
        self,
        field: str,
        value: str,
        locked_by: str,
        rationale: str = "",
    ) -> None:
        """Lock a convention field."""
        state = self.load()
        state.conventions[field] = ConventionLock(
            field=field,
            value=value,
            locked_by=locked_by,
            locked_at=datetime.now(timezone.utc).isoformat(),
            rationale=rationale,
        )
        self.save(state)

    def get_convention(self, field: str) -> str | None:
        """Get a locked convention value."""
        state = self.load()
        lock = state.conventions.get(field)
        return lock.value if lock else None

    def add_decision(
        self,
        phase: str,
        decision: str,
        rationale: str,
        agent: str = "",
    ) -> None:
        """Record a decision."""
        state = self.load()
        state.decisions.append(
            DecisionLogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                phase=phase,
                decision=decision,
                rationale=rationale,
                agent=agent,
            )
        )
        self.save(state)

    def advance_phase(self, phase_id: str) -> None:
        """Mark current phase complete and set next."""
        state = self.load()
        if phase_id in state.phases:
            state.phases[phase_id].status = "completed"
            state.phases[phase_id].completed_at = (
                datetime.now(timezone.utc).isoformat()
            )

        # Find next pending phase
        for pid, phase in state.phases.items():
            if phase.status == "pending":
                state.current_phase = pid
                phase.status = "active"
                phase.started_at = datetime.now(timezone.utc).isoformat()
                break
        else:
            state.current_phase = ""

        self.save(state)

    def set_result(self, key: str, value: Any) -> None:
        """Store an intermediate result for cross-phase access."""
        state = self.load()
        state.results[key] = value
        self.save(state)

    def get_result(self, key: str) -> Any | None:
        """Retrieve an intermediate result."""
        state = self.load()
        return state.results.get(key)
