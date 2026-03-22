"""Observability — session-focused JSONL event logging.

Adapted from GPD's observability.py.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import ProjectLayout


class SessionLogger:
    """JSONL event logger scoped to a session."""

    def __init__(self, layout: ProjectLayout, session_id: str | None = None):
        self.layout = layout
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._session_file: Path | None = None

    def _ensure_dirs(self) -> None:
        self.layout.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self) -> Path:
        if self._session_file is None:
            self._ensure_dirs()
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            self._session_file = (
                self.layout.sessions_dir / f"{timestamp}-{self.session_id}.jsonl"
            )
        return self._session_file

    def _write_current_session(self) -> None:
        """Write current session metadata."""
        self._ensure_dirs()
        meta = {
            "session_id": self.session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "log_file": str(self._get_session_file()),
        }
        current_path = self.layout.observability_dir / "current-session.json"
        current_path.write_text(json.dumps(meta, indent=2))

    def start(self) -> None:
        """Start a new session."""
        self._write_current_session()
        self.log("session_start", {"session_id": self.session_id})

    def log(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Log an event to the session JSONL file."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "type": event_type,
            **(data or {}),
        }
        log_file = self._get_session_file()
        with open(log_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def log_phase_start(self, phase_id: str, title: str) -> None:
        self.log("phase_start", {"phase_id": phase_id, "title": title})

    def log_phase_complete(self, phase_id: str, status: str) -> None:
        self.log("phase_complete", {"phase_id": phase_id, "status": status})

    def log_plan_start(self, phase_id: str, plan_id: str) -> None:
        self.log("plan_start", {"phase_id": phase_id, "plan_id": plan_id})

    def log_plan_complete(self, phase_id: str, plan_id: str, status: str) -> None:
        self.log("plan_complete", {"phase_id": phase_id, "plan_id": plan_id, "status": status})

    def log_task_start(self, task_id: str, title: str) -> None:
        self.log("task_start", {"task_id": task_id, "title": title})

    def log_task_complete(self, task_id: str, status: str) -> None:
        self.log("task_complete", {"task_id": task_id, "status": status})

    def log_verification(self, check_id: str, status: str, message: str) -> None:
        self.log("verification", {"check_id": check_id, "status": status, "message": message})

    def log_convention_lock(self, field: str, value: str) -> None:
        self.log("convention_lock", {"field": field, "value": value})

    def log_decision(self, decision: str, rationale: str) -> None:
        self.log("decision", {"decision": decision, "rationale": rationale})

    def log_backtest(self, strategy: str, metrics: dict[str, Any]) -> None:
        self.log("backtest", {"strategy": strategy, "metrics": metrics})

    def log_error(self, error: str, context: dict[str, Any] | None = None) -> None:
        self.log("error", {"error": error, **(context or {})})

    def end(self) -> None:
        """End the session."""
        self.log("session_end", {"session_id": self.session_id})


class TraceLogger:
    """Plan-local execution trace logger."""

    def __init__(self, layout: ProjectLayout, trace_name: str):
        self.layout = layout
        self.trace_name = trace_name
        self.trace_file = layout.traces_dir / f"{trace_name}.jsonl"
        layout.traces_dir.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace": self.trace_name,
            "type": event_type,
            **(data or {}),
        }
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def start(self) -> None:
        self.log("trace_start")

    def stop(self) -> None:
        self.log("trace_stop")
