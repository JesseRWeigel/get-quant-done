"""MCP server for GQD error handling and observability.

Exposes tools for session logging, error reporting, and trace management.
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

from gqd.core.constants import get_layout, ProjectLayout
from gqd.core.observability import SessionLogger, TraceLogger

server = Server("gqd-errors")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_session_start",
            description="Start a new observability session. Returns session ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Optional session ID. Auto-generated if omitted."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
            },
        ),
        Tool(
            name="gqd_session_log",
            description="Log an event to the current session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "description": "Event type (e.g., error, decision, verification, backtest)."},
                    "data": {"type": "object", "description": "Event data payload."},
                    "session_id": {"type": "string", "description": "Session ID."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["event_type"],
            },
        ),
        Tool(
            name="gqd_error_log",
            description="Log an error with context for debugging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "description": "Error message."},
                    "context": {"type": "object", "description": "Additional context (phase, plan, task, etc.)."},
                    "session_id": {"type": "string", "description": "Session ID."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["error"],
            },
        ),
        Tool(
            name="gqd_session_list",
            description="List recent session log files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max sessions to return. Default 10."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
            },
        ),
        Tool(
            name="gqd_trace_start",
            description="Start a plan-local execution trace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_name": {"type": "string", "description": "Name for the trace (e.g., phase-01-plan-01)."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["trace_name"],
            },
        ),
        Tool(
            name="gqd_trace_log",
            description="Log an event to a named trace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_name": {"type": "string", "description": "Trace name."},
                    "event_type": {"type": "string", "description": "Event type."},
                    "data": {"type": "object", "description": "Event data."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["trace_name", "event_type"],
            },
        ),
    ]


def _layout(project_dir: str | None = None) -> ProjectLayout:
    if project_dir:
        return ProjectLayout(root=Path(project_dir))
    return get_layout()


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "gqd_session_start":
            layout = _layout(arguments.get("project_dir"))
            logger = SessionLogger(layout, arguments.get("session_id"))
            logger.start()
            return [TextContent(type="text", text=json.dumps({
                "status": "ok",
                "session_id": logger.session_id,
                "log_file": str(logger._get_session_file()),
            }))]

        elif name == "gqd_session_log":
            layout = _layout(arguments.get("project_dir"))
            logger = SessionLogger(layout, arguments.get("session_id"))
            logger.log(arguments["event_type"], arguments.get("data"))
            return [TextContent(type="text", text=json.dumps({"status": "ok"}))]

        elif name == "gqd_error_log":
            layout = _layout(arguments.get("project_dir"))
            logger = SessionLogger(layout, arguments.get("session_id"))
            logger.log_error(arguments["error"], arguments.get("context"))
            return [TextContent(type="text", text=json.dumps({"status": "ok", "error": arguments["error"]}))]

        elif name == "gqd_session_list":
            layout = _layout(arguments.get("project_dir"))
            sessions_dir = layout.sessions_dir
            if not sessions_dir.exists():
                return [TextContent(type="text", text=json.dumps({"sessions": []}))]
            limit = arguments.get("limit", 10)
            files = sorted(sessions_dir.glob("*.jsonl"), reverse=True)[:limit]
            sessions = [{"file": str(f), "name": f.name} for f in files]
            return [TextContent(type="text", text=json.dumps({"sessions": sessions}, indent=2))]

        elif name == "gqd_trace_start":
            layout = _layout(arguments.get("project_dir"))
            tracer = TraceLogger(layout, arguments["trace_name"])
            tracer.start()
            return [TextContent(type="text", text=json.dumps({
                "status": "ok",
                "trace_name": arguments["trace_name"],
                "trace_file": str(tracer.trace_file),
            }))]

        elif name == "gqd_trace_log":
            layout = _layout(arguments.get("project_dir"))
            tracer = TraceLogger(layout, arguments["trace_name"])
            tracer.log(arguments["event_type"], arguments.get("data"))
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
