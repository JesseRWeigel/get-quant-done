"""MCP server for GQD project state management.

Exposes tools for loading, saving, and querying the dual-write state engine
(STATE.md + state.json).
"""

from __future__ import annotations

import json
import asyncio
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from gqd.core.constants import get_layout
from gqd.core.state import StateEngine, ProjectState

server = Server("gqd-state")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_state_load",
            description="Load the current GQD project state (phases, conventions, decisions, metrics).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory. Uses cwd if omitted.",
                    }
                },
            },
        ),
        Tool(
            name="gqd_state_set_phase",
            description="Set the current active phase in the project state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID to activate."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase_id"],
            },
        ),
        Tool(
            name="gqd_state_advance_phase",
            description="Mark a phase complete and advance to the next pending phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID to mark complete."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase_id"],
            },
        ),
        Tool(
            name="gqd_state_set_result",
            description="Store an intermediate result for cross-phase access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Result key."},
                    "value": {"type": "string", "description": "Result value (JSON string for complex data)."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["key", "value"],
            },
        ),
        Tool(
            name="gqd_state_get_result",
            description="Retrieve an intermediate result by key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Result key to retrieve."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="gqd_state_add_decision",
            description="Record a decision in the project decision log.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {"type": "string", "description": "Phase the decision belongs to."},
                    "decision": {"type": "string", "description": "The decision made."},
                    "rationale": {"type": "string", "description": "Why this decision was made."},
                    "agent": {"type": "string", "description": "Agent/role that made the decision."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase", "decision", "rationale"],
            },
        ),
    ]


def _engine(project_dir: str | None = None) -> StateEngine:
    if project_dir:
        from gqd.core.constants import ProjectLayout
        return StateEngine(ProjectLayout(root=Path(project_dir)))
    return StateEngine(get_layout())


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "gqd_state_load":
            engine = _engine(arguments.get("project_dir"))
            engine.recover_if_needed()
            state = engine.load()
            return [TextContent(type="text", text=json.dumps(state.model_dump(mode="json"), indent=2))]

        elif name == "gqd_state_set_phase":
            engine = _engine(arguments.get("project_dir"))
            state = engine.load()
            state.current_phase = arguments["phase_id"]
            engine.save(state)
            return [TextContent(type="text", text=json.dumps({"status": "ok", "current_phase": state.current_phase}))]

        elif name == "gqd_state_advance_phase":
            engine = _engine(arguments.get("project_dir"))
            engine.advance_phase(arguments["phase_id"])
            state = engine.load()
            return [TextContent(type="text", text=json.dumps({"status": "ok", "current_phase": state.current_phase}))]

        elif name == "gqd_state_set_result":
            engine = _engine(arguments.get("project_dir"))
            value = arguments["value"]
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            engine.set_result(arguments["key"], value)
            return [TextContent(type="text", text=json.dumps({"status": "ok", "key": arguments["key"]}))]

        elif name == "gqd_state_get_result":
            engine = _engine(arguments.get("project_dir"))
            result = engine.get_result(arguments["key"])
            return [TextContent(type="text", text=json.dumps({"key": arguments["key"], "value": result}))]

        elif name == "gqd_state_add_decision":
            engine = _engine(arguments.get("project_dir"))
            engine.add_decision(
                phase=arguments["phase"],
                decision=arguments["decision"],
                rationale=arguments["rationale"],
                agent=arguments.get("agent", ""),
            )
            return [TextContent(type="text", text=json.dumps({"status": "ok"}))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
