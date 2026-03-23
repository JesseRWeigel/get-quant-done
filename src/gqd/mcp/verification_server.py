"""MCP server for GQD verification kernel.

Exposes tools for running content-addressed verification checks against
evidence registries (no-arbitrage, put-call parity, backtest integrity, etc.).
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

from gqd.core.constants import VERIFICATION_CHECKS
from gqd.core.kernel import VerificationKernel, DEFAULT_PREDICATES, Severity

server = Server("gqd-verification")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gqd_verify_full",
            description="Run ALL verification checks against an evidence registry. Returns SHA-256 verdict.",
            inputSchema={
                "type": "object",
                "properties": {
                    "evidence": {
                        "type": "object",
                        "description": "Evidence registry — key-value pairs consumed by verification predicates.",
                    },
                },
                "required": ["evidence"],
            },
        ),
        Tool(
            name="gqd_verify_single",
            description="Run a single verification check against evidence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "check_id": {
                        "type": "string",
                        "description": f"Check ID. One of: {', '.join(VERIFICATION_CHECKS)}",
                    },
                    "evidence": {
                        "type": "object",
                        "description": "Evidence registry for this check.",
                    },
                },
                "required": ["check_id", "evidence"],
            },
        ),
        Tool(
            name="gqd_verify_list_checks",
            description="List all available verification checks with their severity levels.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="gqd_verify_explain",
            description="Run a check with empty evidence to get suggestions on what evidence is needed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "check_id": {
                        "type": "string",
                        "description": "Check ID to explain.",
                    },
                },
                "required": ["check_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "gqd_verify_full":
            kernel = VerificationKernel()
            verdict = kernel.verify(arguments["evidence"])
            return [TextContent(type="text", text=verdict.to_json())]

        elif name == "gqd_verify_single":
            check_id = arguments["check_id"]
            if check_id not in DEFAULT_PREDICATES:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown check: {check_id}. Available: {list(DEFAULT_PREDICATES.keys())}"}))]
            predicate = DEFAULT_PREDICATES[check_id]
            result = predicate(arguments["evidence"])
            return [TextContent(type="text", text=json.dumps({
                "check_id": result.check_id,
                "name": result.name,
                "status": result.status,
                "severity": result.severity.value,
                "message": result.message,
                "evidence": result.evidence,
                "suggestions": result.suggestions,
            }, indent=2))]

        elif name == "gqd_verify_list_checks":
            # Run all predicates with empty evidence to get severity info
            checks = []
            for check_id, predicate in DEFAULT_PREDICATES.items():
                result = predicate({})
                checks.append({
                    "check_id": check_id,
                    "name": result.name,
                    "severity": result.severity.value,
                    "description": f"Status with no evidence: {result.status} — {result.message}",
                })
            return [TextContent(type="text", text=json.dumps(checks, indent=2))]

        elif name == "gqd_verify_explain":
            check_id = arguments["check_id"]
            if check_id not in DEFAULT_PREDICATES:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown check: {check_id}"}))]
            predicate = DEFAULT_PREDICATES[check_id]
            result = predicate({})
            return [TextContent(type="text", text=json.dumps({
                "check_id": result.check_id,
                "name": result.name,
                "severity": result.severity.value,
                "message": result.message,
                "suggestions": result.suggestions,
            }, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
