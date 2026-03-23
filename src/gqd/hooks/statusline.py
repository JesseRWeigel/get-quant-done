#!/usr/bin/env python3
"""Statusline hook for Claude Code — shows GMD project status.

Adapted from GPD's statusline.py. Reads JSON from stdin (Claude Code
session/hook payload), outputs ANSI-formatted statusline to stdout.

Shows: GMD | model (context size) | [workspace] | current task | P{phase}/{total} | context bar
"""

import json
import math
import os
import sys
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────

_STATUS_LABEL = "GQD"
_STATE_DIR = ".gqd"
_STATE_FILE = "state.json"

# Context bar thresholds (percentage of SCALED usage, not raw)
_CONTEXT_REAL_LIMIT_PCT = 80  # Claude Code compacts at ~80%
_CONTEXT_WARN_THRESHOLD = 63
_CONTEXT_HIGH_THRESHOLD = 81
_CONTEXT_CRITICAL_THRESHOLD = 95

# Field name aliases for Claude Code hook payload
_CONTEXT_REMAINING_KEYS = ("remaining_percentage", "remainingPercent", "remaining")
_CONTEXT_SIZE_KEYS = ("total", "size", "max_tokens")
_MODEL_KEYS = ("name", "id", "model_id")
_WORKSPACE_KEYS = ("cwd", "working_directory", "workspace_dir")
_PROJECT_DIR_KEYS = ("project_dir", "projectDir", "project_path")


# ── Helpers ────────────────────────────────────────────────────────────

def _mapping(value):
    """Return value if it's a dict, else empty dict."""
    return value if isinstance(value, dict) else {}


def _first_string(value, *keys):
    """Return first non-empty string for keys from a mapping."""
    m = _mapping(value)
    for k in keys:
        v = m.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def _first_value(value, *keys):
    """Return first present value for keys from a mapping."""
    m = _mapping(value)
    for k in keys:
        if k in m:
            return m[k]
    return None


# ── Context Bar ────────────────────────────────────────────────────────

def _context_bar(remaining_pct):
    """Build ANSI-colored context-usage bar (scaled to real limit)."""
    rem = round(remaining_pct)
    raw_used = max(0, min(100, 100 - rem))
    used = min(100, round((raw_used / _CONTEXT_REAL_LIMIT_PCT) * 100))

    filled = used // 10
    bar = "\u2588" * filled + "\u2591" * (10 - filled)

    if used < _CONTEXT_WARN_THRESHOLD:
        return f" \x1b[32m{bar} {used}%\x1b[0m"
    if used < _CONTEXT_HIGH_THRESHOLD:
        return f" \x1b[33m{bar} {used}%\x1b[0m"
    if used < _CONTEXT_CRITICAL_THRESHOLD:
        return f" \x1b[38;5;208m{bar} {used}%\x1b[0m"
    return f" \x1b[5;31m\U0001f480 {bar} {used}%\x1b[0m"


# ── Model Label ────────────────────────────────────────────────────────

def _format_context_size(value):
    """Return compact context-window label like '1M context'."""
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return ""
    size = int(value)
    if size >= 1_000_000:
        scaled = size / 1_000_000
        suffix = "M"
    elif size >= 1_000:
        scaled = size / 1_000
        suffix = "k"
    else:
        return f"{size} context"
    if scaled.is_integer() or scaled >= 100:
        compact = f"{scaled:.0f}"
    else:
        compact = f"{scaled:.1f}".rstrip("0").rstrip(".")
    return f"{compact}{suffix} context"


def _read_model_label(data):
    """Return model label with context-window size when available."""
    model_value = data.get("model")
    if isinstance(model_value, str) and model_value:
        model_label = model_value
    else:
        model_label = _first_string(model_value, *_MODEL_KEYS)

    ctx_window = _mapping(data.get("context_window"))
    context_label = _format_context_size(
        _first_value(ctx_window, *_CONTEXT_SIZE_KEYS)
    )
    if model_label and context_label:
        return f"{model_label} ({context_label})"
    return model_label


# ── Workspace Label ────────────────────────────────────────────────────

def _read_workspace_label(data, workspace_dir):
    """Return compact workspace label."""
    if not workspace_dir:
        return ""
    try:
        return f"[{Path(workspace_dir).resolve().name}]"
    except OSError:
        return f"[{workspace_dir}]"


# ── Research Position ──────────────────────────────────────────────────

def _read_position(workspace_dir):
    """Read research position from .gmd/state.json."""
    state_file = Path(workspace_dir) / _STATE_DIR / _STATE_FILE
    if not state_file.exists():
        return ""
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return ""

        # Try GPD-style position object first
        pos = state.get("position", {})
        if isinstance(pos, dict):
            phase = pos.get("current_phase")
            total = pos.get("total_phases")
            if phase is not None and total is not None:
                result = f"P{phase}/{total}"
                plan = pos.get("current_plan")
                total_plans = pos.get("total_plans_in_phase")
                if plan is not None and total_plans is not None:
                    result += f" plan {plan}/{total_plans}"
                return result

        # Fall back to our state format
        current_phase = state.get("current_phase", "")
        phases = state.get("phases", {})
        if isinstance(phases, dict):
            total = len(phases)
            completed = sum(1 for p in phases.values()
                           if isinstance(p, dict) and p.get("status") == "completed")
            if current_phase:
                return f"P{current_phase}/{total} ({completed} done)"
        elif isinstance(phases, list):
            total = len(phases)
            completed = sum(1 for p in phases
                           if isinstance(p, dict) and p.get("status") in ("complete", "completed"))
            current = next((p for p in phases if isinstance(p, dict) and p.get("status") == "active"), None)
            pid = current.get("id", "?") if current else "?"
            return f"P{pid}/{total} ({completed} done)"

        return ""
    except Exception:
        return ""


# ── Current Task ───────────────────────────────────────────────────────

def _read_current_task(session_id, workspace_dir):
    """Find the in-progress task from Claude Code's todo files."""
    if not session_id:
        return ""
    todos_dir = Path(workspace_dir) / ".claude" / "todos" if workspace_dir else None
    if not todos_dir or not todos_dir.is_dir():
        return ""
    try:
        for todo_file in sorted(todos_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
            if not todo_file.name.startswith(f"{session_id}-agent-"):
                continue
            try:
                payload = json.loads(todo_file.read_text(encoding="utf-8"))
                entries = payload if isinstance(payload, list) else [payload]
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("status") == "in_progress":
                        af = entry.get("activeForm")
                        if isinstance(af, str) and af:
                            return af
            except Exception:
                continue
    except Exception:
        pass
    return ""


# ── Workspace from Payload ─────────────────────────────────────────────

def _workspace_from_payload(data):
    """Extract workspace directory from Claude Code hook payload."""
    ws = data.get("workspace")
    if isinstance(ws, str) and ws:
        return ws
    return _first_string(ws, *_WORKSPACE_KEYS) or _first_string(data, *_WORKSPACE_KEYS) or os.getcwd()


# ── Main ───────────────────────────────────────────────────────────────

def main():
    """Entry point: read JSON from stdin, write ANSI statusline to stdout."""
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return

    if not isinstance(data, dict):
        return

    try:
        workspace_dir = _workspace_from_payload(data)
        session_id = data.get("session_id", "")
        if not isinstance(session_id, str):
            session_id = ""

        # Read context remaining
        ctx_window = _mapping(data.get("context_window"))
        remaining = _first_value(ctx_window, *_CONTEXT_REMAINING_KEYS)
        ctx = _context_bar(remaining) if isinstance(remaining, (int, float)) and math.isfinite(remaining) else ""

        # Read other fields
        model_label = _read_model_label(data)
        workspace_label = _read_workspace_label(data, workspace_dir)
        position = _read_position(workspace_dir)
        task = _read_current_task(session_id, workspace_dir)

        # Build segments
        segments = [f"\x1b[2m{_STATUS_LABEL}\x1b[0m"]
        if model_label:
            segments.append(model_label)
        if workspace_label:
            segments.append(f"\x1b[2m{workspace_label}\x1b[0m")
        if task:
            segments.append(f"\x1b[1m{task}\x1b[0m")
        if position:
            segments.append(f"\x1b[36m{position}\x1b[0m")

        statusline = " \u2502 ".join(segments)
        sys.stdout.write(statusline)
        if ctx:
            sys.stdout.write(ctx)
    except Exception:
        sys.stdout.write(f"\x1b[2m{_STATUS_LABEL}\x1b[0m")


if __name__ == "__main__":
    main()
