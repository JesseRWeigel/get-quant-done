"""Phase lifecycle — ROADMAP.md parsing, wave validation, dependency DAG.

Quantitative finance research decomposes into phases:
  1. Literature survey / known results
  2. Model specification (pricing model, assumptions, conventions)
  3. Analytical derivation (closed-form solutions, approximations)
  4. Numerical implementation (Monte Carlo, PDE solvers, optimizers)
  5. Backtesting and empirical validation
  6. Robustness and sensitivity analysis
  7. Paper writing and submission
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import ProjectLayout, PLAN_PREFIX, SUMMARY_PREFIX
from .state import StateEngine, PhaseState


@dataclass
class Task:
    """A single atomic work unit within a plan."""

    id: str
    title: str
    description: str = ""
    status: str = "pending"  # pending | in_progress | completed | skipped
    depends_on: list[str] = field(default_factory=list)
    wave: int = 0  # Assigned during wave computation


@dataclass
class Plan:
    """A PLAN.md file — a set of tasks for a portion of a phase."""

    id: str  # e.g., "01-01"
    phase_id: str
    title: str
    goal: str = ""
    tasks: list[Task] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)  # Other plan IDs
    status: str = "pending"


@dataclass
class Wave:
    """A group of plans/tasks that can execute in parallel."""

    number: int
    plans: list[Plan] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Phase:
    """A research phase with plans grouped into waves."""

    id: str
    title: str
    goal: str = ""
    plans: list[Plan] = field(default_factory=list)
    waves: list[Wave] = field(default_factory=list)


def parse_roadmap(roadmap_path: Path) -> list[Phase]:
    """Parse ROADMAP.md into Phase objects.

    Expected format:
    ## Phase 1: Literature Survey
    **Goal**: Identify known results and open problems in [topic]

    ### Plans
    - Plan 01-01: Search SSRN for [topic]
    - Plan 01-02: Survey arXiv q-fin preprints
      - depends: 01-01
    """
    if not roadmap_path.exists():
        return []

    content = roadmap_path.read_text()
    phases: list[Phase] = []
    current_phase: Phase | None = None

    for line in content.splitlines():
        # Phase header: ## Phase N: Title
        phase_match = re.match(r"^##\s+Phase\s+(\S+):\s+(.+)", line)
        if phase_match:
            current_phase = Phase(
                id=phase_match.group(1),
                title=phase_match.group(2).strip(),
            )
            phases.append(current_phase)
            continue

        if current_phase is None:
            continue

        # Goal line
        goal_match = re.match(r"^\*\*Goal\*\*:\s+(.+)", line)
        if goal_match:
            current_phase.goal = goal_match.group(1).strip()
            continue

        # Plan line: - Plan XX-YY: Title
        plan_match = re.match(r"^\s*-\s+Plan\s+(\S+):\s+(.+)", line)
        if plan_match:
            plan = Plan(
                id=plan_match.group(1),
                phase_id=current_phase.id,
                title=plan_match.group(2).strip(),
            )
            current_phase.plans.append(plan)
            continue

        # Dependency line:   - depends: XX-YY, XX-ZZ
        dep_match = re.match(r"^\s+-\s+depends:\s+(.+)", line)
        if dep_match and current_phase.plans:
            deps = [d.strip() for d in dep_match.group(1).split(",")]
            current_phase.plans[-1].depends_on = deps

    return phases


def compute_waves(plans: list[Plan]) -> list[Wave]:
    """Group plans into dependency-ordered waves.

    Plans with no unmet dependencies go into wave 1.
    Plans depending only on wave-1 plans go into wave 2, etc.
    """
    if not plans:
        return []

    plan_ids = {p.id for p in plans}
    assigned: dict[str, int] = {}
    waves: dict[int, list[Plan]] = {}

    max_iterations = len(plans) + 1
    iteration = 0

    while len(assigned) < len(plans) and iteration < max_iterations:
        iteration += 1
        wave_num = iteration

        for plan in plans:
            if plan.id in assigned:
                continue

            # Check if all dependencies are assigned to earlier waves
            deps_met = all(
                dep in assigned and assigned[dep] < wave_num
                for dep in plan.depends_on
                if dep in plan_ids
            )

            if deps_met:
                assigned[plan.id] = wave_num
                waves.setdefault(wave_num, []).append(plan)

    # Build Wave objects
    result = []
    for wave_num in sorted(waves.keys()):
        result.append(Wave(number=wave_num, plans=waves[wave_num]))

    return result


def compute_task_waves(tasks: list[Task]) -> list[Wave]:
    """Group tasks within a plan into dependency-ordered waves."""
    if not tasks:
        return []

    task_ids = {t.id for t in tasks}
    assigned: dict[str, int] = {}
    waves: dict[int, list[Task]] = {}

    max_iterations = len(tasks) + 1
    iteration = 0

    while len(assigned) < len(tasks) and iteration < max_iterations:
        iteration += 1
        wave_num = iteration

        for task in tasks:
            if task.id in assigned:
                continue

            deps_met = all(
                dep in assigned and assigned[dep] < wave_num
                for dep in task.depends_on
                if dep in task_ids
            )

            if deps_met:
                assigned[task.id] = wave_num
                task.wave = wave_num
                waves.setdefault(wave_num, []).append(task)

    result = []
    for wave_num in sorted(waves.keys()):
        result.append(Wave(number=wave_num, tasks=waves[wave_num]))

    return result


def discover_plans(layout: ProjectLayout, phase_id: str) -> list[Path]:
    """Find all PLAN-*.md files for a given phase."""
    phase_dir = layout.phase_dir(phase_id)
    if not phase_dir.exists():
        return []

    plans = sorted(phase_dir.glob(f"{PLAN_PREFIX}-*.md"))
    return plans


def discover_summaries(layout: ProjectLayout, phase_id: str) -> list[Path]:
    """Find all SUMMARY-*.md files for a given phase."""
    phase_dir = layout.phase_dir(phase_id)
    if not phase_dir.exists():
        return []

    return sorted(phase_dir.glob(f"{SUMMARY_PREFIX}-*.md"))


def parse_plan_file(plan_path: Path) -> Plan:
    """Parse a PLAN-XX-YY.md file into a Plan object.

    Expected format:
    ---
    phase: 1
    plan: 01-01
    title: Calibrate pricing model
    goal: Calibrate Heston model to SPX options data
    depends_on: []
    ---

    ## Tasks

    ### Task 1: Download option chain data
    Description of what to do.
    - depends: []

    ### Task 2: Implement calibration routine
    Description.
    - depends: [1]
    """
    content = plan_path.read_text()

    # Parse YAML frontmatter
    fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    metadata: dict[str, Any] = {}
    if fm_match:
        for line in fm_match.group(1).splitlines():
            kv = line.split(":", 1)
            if len(kv) == 2:
                key = kv[0].strip()
                val = kv[1].strip()
                metadata[key] = val

    plan_id = metadata.get("plan", plan_path.stem.replace(PLAN_PREFIX + "-", ""))
    phase_id = metadata.get("phase", "")

    plan = Plan(
        id=plan_id,
        phase_id=phase_id,
        title=metadata.get("title", ""),
        goal=metadata.get("goal", ""),
    )

    # Parse tasks
    task_pattern = re.compile(r"^###\s+Task\s+(\S+):\s+(.+)", re.MULTILINE)
    dep_pattern = re.compile(r"^\s*-\s+depends:\s*\[(.+?)\]", re.MULTILINE)

    task_matches = list(task_pattern.finditer(content))
    for i, match in enumerate(task_matches):
        task_id = match.group(1)
        title = match.group(2).strip()

        # Get description (text between this task and next task/end)
        start = match.end()
        end = task_matches[i + 1].start() if i + 1 < len(task_matches) else len(content)
        section = content[start:end]

        # Check for dependencies
        deps: list[str] = []
        dep_match = dep_pattern.search(section)
        if dep_match:
            deps = [d.strip() for d in dep_match.group(1).split(",") if d.strip()]

        description = section.strip()
        # Remove the depends line from description
        if dep_match:
            description = section[: dep_match.start()].strip()

        plan.tasks.append(
            Task(
                id=task_id,
                title=title,
                description=description,
                depends_on=deps,
            )
        )

    return plan
