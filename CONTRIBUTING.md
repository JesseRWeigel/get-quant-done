# Contributing to get-quant-done

Thank you for your interest in contributing to **get-quant-done** — an AI copilot for autonomous quantitative finance research.
This guide covers everything you need to get started.

## Table of Contents

1. [Dev Environment Setup](#dev-environment-setup)
2. [Project Structure](#project-structure)
3. [Adding a New Protocol](#adding-a-new-protocol)
4. [Adding a New Agent](#adding-a-new-agent)
5. [Adding a Verification Check](#adding-a-verification-check)
6. [Implementing an MCP Server](#implementing-an-mcp-server)
7. [Testing](#testing)
8. [Code Style](#code-style)
9. [Pull Request Process](#pull-request-process)
10. [GPD Architecture Reference](#gpd-architecture-reference)

## Dev Environment Setup

```bash
# Clone the repository
git clone https://github.com/JesseRWeigel/get-quant-done.git
cd get-quant-done

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate  # Windows

# Install in editable mode
pip install -e .
```

Verify the install:

```bash
gqd --help
```

## Project Structure

```
get-quant-done/
├── pyproject.toml
├── src/
│   └── gqd/
│       ├── __init__.py
│       ├── contracts.py          # Pydantic models for inter-agent data
│       ├── core/
│       │   ├── config.py         # Runtime configuration
│       │   ├── constants.py      # All magic strings and env vars
│       │   ├── conventions.py    # File / naming conventions
│       │   ├── git_ops.py        # Git helpers
│       │   ├── kernel.py         # Content-addressed verification kernel
│       │   └── observability.py  # Logging and tracing
│       ├── agents/               # Agent definitions (Markdown + YAML frontmatter)
│       ├── commands/             # CLI command specs (Markdown)
│       └── specs/
│           └── references/
│               ├── orchestration/ # Agent delegation specs
│               ├── protocols/    # Domain methodology protocols
│               └── verification/ # LLM error patterns
├── bin/                          # Helper scripts
└── infra/                        # Infrastructure configs
```

## Adding a New Protocol

Protocols live in `src/gqd/specs/references/protocols/`. Each file encodes a
domain methodology that agents follow during execution.

Existing protocols:
  - `backtesting-protocols.md`
  - `option-pricing-protocols.md`

To add a new one:

1. Create a Markdown file in `src/gqd/specs/references/protocols/`, e.g.
   `backtesting-methodology-protocols.md`.
2. Use YAML frontmatter to declare metadata:

   ```markdown
   ---
   domain: backtesting methodology
   version: "0.1"
   ---

   # Backtesting Methodology Protocols

   ## Overview
   Describe the methodology...

   ## Steps
   1. ...
   ```

3. Reference the protocol from any agent that needs it (in the agent's `tools` list).

## Adding a New Agent

Agents are Markdown files with YAML frontmatter in `src/gqd/agents/`.

Current agents:
  - `gqd-backtester.md`
  - `gqd-executor.md`
  - `gqd-paper-writer.md`
  - `gqd-planner.md`
  - `gqd-referee.md`
  - `gqd-researcher.md`
  - `gqd-verifier.md`

To add a new agent:

1. Create `src/gqd/agents/gqd-risk-analyst.md`.
2. Include the required YAML frontmatter:

   ```markdown
   ---
   name: gqd-risk-analyst
   description: One-line description of the agent's purpose
   tools: [gqd-state, gqd-conventions, gqd-protocols]
   commit_authority: orchestrator
   surface: internal
   role_family: analysis
   artifact_write_authority: scoped_write
   shared_state_authority: return_only
   ---

   <role>
   You are the **GQD Risk Analyst** — ...
   </role>
   ```

3. Key frontmatter fields:
   - `name` — must match the filename (without `.md`)
   - `tools` — list of tool prefixes the agent may invoke
   - `commit_authority` — who may commit (`orchestrator` | `self`)
   - `surface` — `internal` (other agents only) or `external` (user-facing)
   - `role_family` — `analysis`, `execution`, `verification`, or `writing`

## Adding a Verification Check

Verification predicates live in `src/gqd/core/kernel.py`. Each check is a
function that inspects evidence and returns a `CheckResult`.

To add a new check:

1. Open `src/gqd/core/kernel.py`.
2. Add a predicate function:

   ```python
   def check_backtest_validity(evidence: dict[str, Any]) -> CheckResult:
       """Checks for look-ahead bias and survivorship bias in backtests."""
       # Inspect evidence...
       passed = ...  # your logic
       return CheckResult(
           check_id="backtest_validity",
           name="Backtest Validity",
           status="PASS" if passed else "FAIL",
           severity=Severity.MAJOR,
           message="..." if not passed else "",
       )
   ```

3. Register the check in `constants.py` under `VERIFICATION_CHECKS`.
4. Write a corresponding test (see [Testing](#testing)).

## Implementing an MCP Server

MCP (Model Context Protocol) servers expose tool endpoints that agents can call at
runtime. To add one:

1. Create a Python module under `src/gqd/mcp/`, e.g.
   `src/gqd/mcp/risk-analyst_server.py`.
2. Implement the server using the MCP SDK:

   ```python
   from mcp.server import Server

   server = Server("gqd-risk-analyst")

   @server.tool()
   async def my_tool(param: str) -> str:
       """Description of what this tool does."""
       ...
   ```

3. Register the server in the project's configuration so agents can discover it.
4. Document the server's tools in a companion Markdown file.

## Testing

Run the full test suite:

```bash
python -m pytest
```

Run a specific test file:

```bash
python -m pytest tests/test_kernel.py -v
```

When contributing, please:

- Add tests for new verification checks.
- Add tests for new MCP server tools.
- Ensure all existing tests pass before opening a PR.

## Code Style

### Python

- **Type hints** on all function signatures.
- **Pydantic models** (`BaseModel`) for structured data that crosses boundaries
  (see `contracts.py`).
- Follow existing patterns in `core/` for new modules.
- Use `from __future__ import annotations` at the top of every module.

### Markdown

- Agent and protocol files **must** have YAML frontmatter (`---` delimiters).
- Use ATX-style headings (`#`, `##`, `###`).
- Wrap prose at ~100 characters where practical.

### General

- Keep commits focused — one logical change per commit.
- Use clear, descriptive commit messages.

## Pull Request Process

1. **Fork** the repo and create a feature branch from `master`.
2. Make your changes following the guidelines above.
3. Ensure `python -m pytest` passes locally.
4. Open a Pull Request against `master` with:
   - A clear title summarizing the change.
   - A description of *what* and *why*.
   - Links to any related issues.
5. A maintainer will review your PR. Please be responsive to feedback.
6. Once approved, a maintainer will merge.

## GPD Architecture Reference

get-quant-done follows the **Get-Paper-Done (GPD)** architecture — a shared framework
across the `get-*-done` family of research copilots. Key architectural concepts:

| Concept | Description |
|---|---|
| **Kernel** | Content-addressed verification engine (`kernel.py`) producing SHA-256 verdicts |
| **Agents** | Markdown-defined roles with YAML frontmatter controlling capabilities |
| **Protocols** | Domain methodology references that agents follow during execution |
| **Contracts** | Pydantic models defining the data exchanged between agents |
| **Commands** | CLI entry points that orchestrate agent workflows |
| **Observability** | Structured logging and tracing for debugging agent runs |

For the full specification, see the
[get-paper-done](https://github.com/JesseRWeigel/get-paper-done) repository.
