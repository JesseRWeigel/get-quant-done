"""MCP server for GQD research contracts and patterns.

Exposes tools for managing research contracts (claims, deliverables,
acceptance tests, forbidden proxies) and agent return envelopes.
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

from gqd.core.config import GQDConfig, MODEL_PROFILES, RESEARCH_MODE_PARAMS
from gqd.core.constants import get_layout, ProjectLayout, CONVENTION_FIELDS, VERIFICATION_CHECKS

server = Server("gqd-patterns")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_config_load",
            description="Load the GQD project configuration (model profile, autonomy, research mode).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project root directory."},
                },
            },
        ),
        Tool(
            name="gqd_config_profiles",
            description="List available model profiles with their tier assignments per role.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="gqd_config_research_modes",
            description="List available research modes with their parameters.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="gqd_contract_template",
            description="Generate a research contract template for a phase/plan.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "Phase ID."},
                    "plan_id": {"type": "string", "description": "Plan ID (optional)."},
                    "goal": {"type": "string", "description": "Goal of the research contract."},
                },
                "required": ["phase_id", "goal"],
            },
        ),
        Tool(
            name="gqd_agent_return_template",
            description="Generate an AgentReturn envelope template for structured subagent responses.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="gqd_domain_summary",
            description="Get a summary of all GQD domain concepts: convention fields, verification checks, model profiles.",
            inputSchema={
                "type": "object",
                "properties": {},
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
        if name == "gqd_config_load":
            layout = _layout(arguments.get("project_dir"))
            config = GQDConfig.load(layout)
            errors = config.validate()
            return [TextContent(type="text", text=json.dumps({
                "model_profile": config.model_profile,
                "autonomy": config.autonomy,
                "research_mode": config.research_mode,
                "commit_docs": config.commit_docs,
                "workflow": config.workflow,
                "research_params": config.get_research_params(),
                "validation_errors": errors,
            }, indent=2))]

        elif name == "gqd_config_profiles":
            result = {}
            for profile_name, roles in MODEL_PROFILES.items():
                result[profile_name] = roles
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "gqd_config_research_modes":
            return [TextContent(type="text", text=json.dumps(RESEARCH_MODE_PARAMS, indent=2))]

        elif name == "gqd_contract_template":
            template = {
                "phase_id": arguments["phase_id"],
                "plan_id": arguments.get("plan_id", ""),
                "goal": arguments["goal"],
                "claims": [
                    {"id": "C1", "statement": "<claim to validate>", "claim_type": "proposition", "assumptions": [], "depends_on": [], "status": "unvalidated"},
                ],
                "deliverables": [
                    {"id": "D1", "description": "<artifact to produce>", "artifact_type": "implementation", "file_path": "", "acceptance_tests": ["T1"], "status": "pending"},
                ],
                "acceptance_tests": [
                    {"id": "T1", "description": "<what to test>", "test_type": "verification", "predicate": "<condition>", "status": "pending"},
                ],
                "forbidden_proxies": [
                    {"description": "Agent stating 'model is correct' without derivation", "reason": "Full derivation must exist on disk and pass verification."},
                    {"description": "Backtest results without out-of-sample validation", "reason": "In-sample performance alone is not evidence of strategy validity."},
                    {"description": "Pricing formula without no-arbitrage verification", "reason": "All pricing models must satisfy no-arbitrage conditions."},
                ],
            }
            return [TextContent(type="text", text=json.dumps(template, indent=2))]

        elif name == "gqd_agent_return_template":
            template = {
                "status": "completed | checkpoint | blocked | failed",
                "files_written": [],
                "files_modified": [],
                "issues": [],
                "next_actions": [],
                "claims_validated": [],
                "conventions_proposed": {},
                "verification_evidence": {},
            }
            return [TextContent(type="text", text=json.dumps(template, indent=2))]

        elif name == "gqd_domain_summary":
            summary = {
                "convention_fields": CONVENTION_FIELDS,
                "verification_checks": VERIFICATION_CHECKS,
                "model_profiles": list(MODEL_PROFILES.keys()),
                "research_modes": list(RESEARCH_MODE_PARAMS.keys()),
                "domain": "quantitative finance",
                "description": (
                    "GQD (get-quant-done) is a framework for structured quantitative finance "
                    "research. It manages model assumptions via convention locks, verifies "
                    "financial correctness (no-arbitrage, put-call parity, backtest integrity), "
                    "and tracks research phases from literature survey through paper writing."
                ),
            }
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
