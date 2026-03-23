"""MCP server for GQD phase/plan protocols.

Exposes tools for parsing ROADMAP.md, computing dependency waves,
discovering plans, and managing the phase lifecycle.
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
from gqd.core.phases import (
    parse_roadmap,
    compute_waves,
    discover_plans,
    discover_summaries,
    parse_plan_file,
)

server = Server("gqd-protocols")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_roadmap_parse",
            description="Parse ROADMAP.md into phases with their plans and dependency structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
            },
        ),
        Tool(
            name="gqd_waves_compute",
            description="Compute dependency-ordered execution waves for a phase's plans.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID to compute waves for."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase_id"],
            },
        ),
        Tool(
            name="gqd_plans_discover",
            description="Find all PLAN-*.md files for a given phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase_id"],
            },
        ),
        Tool(
            name="gqd_plan_parse",
            description="Parse a PLAN-*.md file into structured tasks with dependencies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_path": {"type": "string", "description": "Absolute path to the PLAN-*.md file."},
                },
                "required": ["plan_path"],
            },
        ),
        Tool(
            name="gqd_summaries_discover",
            description="Find all SUMMARY-*.md files for a given phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID."},
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
                "required": ["phase_id"],
            },
        ),
    ]


def _layout(project_dir: str | None = None) -> ProjectLayout:
    if project_dir:
        return ProjectLayout(root=Path(project_dir))
    return get_layout()


def _phase_to_dict(phase) -> dict:
    return {
        "id": phase.id,
        "title": phase.title,
        "goal": phase.goal,
        "plans": [
            {"id": p.id, "title": p.title, "depends_on": p.depends_on}
            for p in phase.plans
        ],
    }


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "gqd_roadmap_parse":
            layout = _layout(arguments.get("project_dir"))
            phases = parse_roadmap(layout.roadmap_md)
            result = [_phase_to_dict(p) for p in phases]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "gqd_waves_compute":
            layout = _layout(arguments.get("project_dir"))
            phases = parse_roadmap(layout.roadmap_md)
            target = None
            for p in phases:
                if p.id == arguments["phase_id"]:
                    target = p
                    break
            if not target:
                return [TextContent(type="text", text=json.dumps({"error": f"Phase {arguments['phase_id']} not found"}))]
            waves = compute_waves(target.plans)
            result = [
                {"wave": w.number, "plans": [{"id": p.id, "title": p.title} for p in w.plans]}
                for w in waves
            ]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "gqd_plans_discover":
            layout = _layout(arguments.get("project_dir"))
            plans = discover_plans(layout, arguments["phase_id"])
            return [TextContent(type="text", text=json.dumps([str(p) for p in plans]))]

        elif name == "gqd_plan_parse":
            plan = parse_plan_file(Path(arguments["plan_path"]))
            result = {
                "id": plan.id,
                "phase_id": plan.phase_id,
                "title": plan.title,
                "goal": plan.goal,
                "tasks": [
                    {"id": t.id, "title": t.title, "description": t.description, "depends_on": t.depends_on, "status": t.status}
                    for t in plan.tasks
                ],
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "gqd_summaries_discover":
            layout = _layout(arguments.get("project_dir"))
            summaries = discover_summaries(layout, arguments["phase_id"])
            return [TextContent(type="text", text=json.dumps([str(s) for s in summaries]))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
