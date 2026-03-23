#!/usr/bin/env python3
"""Statusline hook for Claude Code — shows GQD project status.

Reads JSON from stdin (Claude Code session data), outputs ANSI-formatted
statusline with: GQD | model | phase/plan progress | context bar

Adapted from GPD's statusline.py.
"""

import json
import sys
import os


def context_bar(used_pct: float, width: int = 20) -> str:
    """Render a visual context usage bar."""
    filled = int(used_pct / 100 * width)
    empty = width - filled

    if used_pct < 50:
        color = "\033[32m"  # green
    elif used_pct < 80:
        color = "\033[33m"  # yellow
    else:
        color = "\033[31m"  # red

    reset = "\033[0m"
    bar = "█" * filled + "░" * empty
    return f"{color}{bar}{reset} {used_pct:.0f}%"


def get_phase_info() -> str:
    """Try to read current phase from STATE.md or state.json."""
    # Look for .gqd directory
    cwd = os.getcwd()
    search = cwd
    while search != os.path.dirname(search):
        state_json = os.path.join(search, ".gqd", "state.json")
        if os.path.exists(state_json):
            try:
                with open(state_json) as f:
                    state = json.load(f)
                phase = state.get("current_phase", "")
                plan = state.get("current_plan", "")
                milestone = state.get("current_milestone", "")

                # Count phase progress
                phases = state.get("phases", {})
                completed = sum(1 for p in phases.values() if isinstance(p, dict) and p.get("status") == "completed")
                total = len(phases)

                parts = []
                if milestone:
                    parts.append(milestone)
                if phase:
                    parts.append(f"P{phase}")
                if plan:
                    parts.append(f"plan:{plan}")
                if total > 0:
                    parts.append(f"{completed}/{total}")

                return " ".join(parts) if parts else ""
            except (json.JSONDecodeError, KeyError, IOError):
                return ""
        search = os.path.dirname(search)
    return ""


def format_statusline(data: dict) -> str:
    """Format the statusline from Claude Code session data."""
    parts = []

    # Brand
    parts.append("\033[1;36mGQD\033[0m")  # bold cyan

    # Model info
    model = data.get("model", "")
    if model:
        # Shorten model name
        short = model.replace("claude-", "").replace("anthropic/", "")
        parts.append(short)

    # Phase info from state
    phase_info = get_phase_info()
    if phase_info:
        parts.append(f"\033[33m{phase_info}\033[0m")  # yellow

    # Context usage
    context_used = data.get("context_used", 0)
    context_total = data.get("context_total", 0)
    if context_total > 0:
        pct = (context_used / context_total) * 100
        parts.append(context_bar(pct))
    elif "context_percent" in data:
        parts.append(context_bar(data["context_percent"]))

    return " │ ".join(parts)


def main():
    """Read session data from stdin, output statusline."""
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            print("GQD")
            return

        data = json.loads(raw)
        print(format_statusline(data))
    except (json.JSONDecodeError, KeyError):
        print("GQD")
    except Exception:
        print("GQD")


if __name__ == "__main__":
    main()
