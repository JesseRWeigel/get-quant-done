"""MCP server for GQD convention lock management.

Exposes tools for locking, querying, and diffing quantitative finance
model assumptions (pricing model, risk-free rate, day count, etc.).
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

from gqd.core.constants import get_layout, CONVENTION_FIELDS, ProjectLayout
from gqd.core.state import StateEngine
from gqd.core.conventions import (
    list_all_fields,
    check_conventions,
    diff_conventions,
    get_field_description,
    get_field_examples,
)

server = Server("gqd-conventions")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_conventions_list",
            description="List all quantitative finance convention fields with descriptions and examples.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="gqd_conventions_check",
            description="Check which conventions are locked and which are missing. Returns coverage stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
            },
        ),
        Tool(
            name="gqd_conventions_lock",
            description="Lock a convention field to a specific value (e.g., pricing_model = 'Black-Scholes').",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": f"Convention field. One of: {', '.join(CONVENTION_FIELDS)}"},
                    "value": {"type": "string", "description": "Value to lock."},
                    "locked_by": {"type": "string", "description": "Phase/plan that locks this convention."},
                    "rationale": {"type": "string", "description": "Why this value was chosen."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["field", "value", "locked_by"],
            },
        ),
        Tool(
            name="gqd_conventions_get",
            description="Get the current locked value for a specific convention field.",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "Convention field name."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["field"],
            },
        ),
        Tool(
            name="gqd_conventions_diff",
            description="Compare proposed convention values against current locks. Identifies conflicts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "proposed": {
                        "type": "object",
                        "description": "Map of field names to proposed values.",
                        "additionalProperties": {"type": "string"},
                    },
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["proposed"],
            },
        ),
    ]


def _engine(project_dir: str | None = None) -> StateEngine:
    if project_dir:
        return StateEngine(ProjectLayout(root=Path(project_dir)))
    return StateEngine(get_layout())


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "gqd_conventions_list":
            fields = list_all_fields()
            return [TextContent(type="text", text=json.dumps(fields, indent=2))]

        elif name == "gqd_conventions_check":
            engine = _engine(arguments.get("project_dir"))
            report = check_conventions(engine)
            return [TextContent(type="text", text=json.dumps(report, indent=2))]

        elif name == "gqd_conventions_lock":
            engine = _engine(arguments.get("project_dir"))
            engine.set_convention(
                field=arguments["field"],
                value=arguments["value"],
                locked_by=arguments["locked_by"],
                rationale=arguments.get("rationale", ""),
            )
            return [TextContent(type="text", text=json.dumps({"status": "ok", "field": arguments["field"], "value": arguments["value"]}))]

        elif name == "gqd_conventions_get":
            engine = _engine(arguments.get("project_dir"))
            value = engine.get_convention(arguments["field"])
            desc = get_field_description(arguments["field"])
            examples = get_field_examples(arguments["field"])
            return [TextContent(type="text", text=json.dumps({
                "field": arguments["field"],
                "value": value,
                "description": desc,
                "examples": examples,
            }, indent=2))]

        elif name == "gqd_conventions_diff":
            engine = _engine(arguments.get("project_dir"))
            result = diff_conventions(engine, arguments["proposed"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
