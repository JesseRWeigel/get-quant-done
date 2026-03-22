"""Git operations — atomic commits with pre-commit checks and ratcheting.

Adapted from GPD's git_ops.py for quantitative finance research.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .constants import (
    CHECKPOINT_TAG_PREFIX,
    COMMIT_PREFIX,
    GQD_DIR,
    SCRATCH_DIR,
    ProjectLayout,
)


class GitError(Exception):
    """Git operation failed."""


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repository."""
    try:
        _run_git(["rev-parse", "--git-dir"], cwd=path)
        return True
    except (GitError, FileNotFoundError):
        return False


def init_repo(path: Path) -> None:
    """Initialize a git repository if one doesn't exist."""
    if not is_git_repo(path):
        _run_git(["init"], cwd=path)


# -- Pre-commit Checks -------------------------------------------------------

def check_no_scratch_files(layout: ProjectLayout, files: list[str]) -> list[str]:
    """Ensure no scratch/temporary files are being committed."""
    violations = []
    scratch = str(layout.scratch_dir.relative_to(layout.root))
    for f in files:
        if f.startswith(scratch) or f.startswith(SCRATCH_DIR):
            violations.append(f"Scratch file staged: {f}")
    return violations


def check_no_nan_inf(layout: ProjectLayout, files: list[str]) -> list[str]:
    """Check for NaN/Inf in JSON and data files."""
    violations = []
    for f in files:
        path = layout.root / f
        if path.suffix in (".json", ".csv", ".tsv") and path.exists():
            content = path.read_text()
            if re.search(r'\bNaN\b|\bInfinity\b|\b-Infinity\b', content):
                violations.append(f"NaN/Inf detected in {f}")
    return violations


def check_frontmatter_yaml(layout: ProjectLayout, files: list[str]) -> list[str]:
    """Check that .md files with frontmatter have valid YAML."""
    violations = []
    for f in files:
        path = layout.root / f
        if path.suffix == ".md" and path.exists():
            content = path.read_text()
            if content.startswith("---\n"):
                end = content.find("\n---\n", 4)
                if end == -1:
                    violations.append(f"Unclosed YAML frontmatter in {f}")
    return violations


def check_no_api_keys(layout: ProjectLayout, files: list[str]) -> list[str]:
    """Check for accidentally committed API keys or secrets."""
    violations = []
    key_patterns = [
        r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][A-Za-z0-9+/=]{20,}',
        r'sk-[A-Za-z0-9]{20,}',  # OpenAI-style keys
        r'AKIA[0-9A-Z]{16}',      # AWS access keys
    ]
    for f in files:
        path = layout.root / f
        if path.suffix in (".py", ".json", ".yaml", ".yml", ".env", ".toml") and path.exists():
            content = path.read_text()
            for pattern in key_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(f"Potential API key/secret in {f}")
                    break
    return violations


def run_pre_commit_checks(layout: ProjectLayout, files: list[str]) -> list[str]:
    """Run all pre-commit checks. Returns list of violation messages."""
    violations = []
    violations.extend(check_no_scratch_files(layout, files))
    violations.extend(check_no_nan_inf(layout, files))
    violations.extend(check_frontmatter_yaml(layout, files))
    violations.extend(check_no_api_keys(layout, files))
    return violations


# -- Commit Operations --------------------------------------------------------

def get_staged_files(cwd: Path) -> list[str]:
    """Get list of staged files."""
    output = _run_git(["diff", "--cached", "--name-only"], cwd=cwd)
    return [f for f in output.splitlines() if f]


def commit(
    layout: ProjectLayout,
    message: str,
    files: list[str] | None = None,
    skip_checks: bool = False,
) -> str:
    """Make an atomic commit with pre-commit checks.

    Returns the commit hash.
    """
    cwd = layout.root

    # Stage files if specified
    if files:
        for f in files:
            _run_git(["add", f], cwd=cwd)

    # Get staged files
    staged = get_staged_files(cwd)
    if not staged:
        raise GitError("Nothing to commit.")

    # Run pre-commit checks
    if not skip_checks:
        violations = run_pre_commit_checks(layout, staged)
        if violations:
            raise GitError(
                "Pre-commit checks failed:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )

    # Commit with prefix
    full_message = f"{COMMIT_PREFIX} {message}"
    _run_git(["commit", "-m", full_message], cwd=cwd)

    # Return hash
    return _run_git(["rev-parse", "HEAD"], cwd=cwd)


# -- Ratcheting ---------------------------------------------------------------

def create_checkpoint_tag(
    layout: ProjectLayout,
    phase: str,
    plan: str,
) -> str:
    """Create a rollback checkpoint tag before plan execution."""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    tag = f"{CHECKPOINT_TAG_PREFIX}/phase-{phase}-plan-{plan}-{timestamp}"
    _run_git(["tag", tag], cwd=layout.root)
    return tag


def rollback_to_tag(layout: ProjectLayout, tag: str) -> None:
    """Rollback to a checkpoint tag."""
    _run_git(["reset", "--hard", tag], cwd=layout.root)


def list_checkpoint_tags(layout: ProjectLayout) -> list[str]:
    """List all checkpoint tags, newest first."""
    try:
        output = _run_git(
            ["tag", "--list", f"{CHECKPOINT_TAG_PREFIX}/*", "--sort=-creatordate"],
            cwd=layout.root,
        )
        return [t for t in output.splitlines() if t]
    except GitError:
        return []


def find_partial_completion(
    layout: ProjectLayout,
    phase: str,
    plan: str,
) -> list[str]:
    """Find commits for a partially completed plan.

    Searches git log for [gqd] commits matching the phase/plan.
    Returns list of commit hashes.
    """
    try:
        output = _run_git(
            [
                "log",
                "--oneline",
                f"--grep={COMMIT_PREFIX}.*phase-{phase}.*plan-{plan}",
                "--format=%H",
            ],
            cwd=layout.root,
        )
        return [h for h in output.splitlines() if h]
    except GitError:
        return []


# -- Utilities ----------------------------------------------------------------

def has_uncommitted_changes(layout: ProjectLayout) -> bool:
    """Check for uncommitted changes."""
    output = _run_git(["status", "--porcelain"], cwd=layout.root)
    return bool(output.strip())


def uncommitted_file_count(layout: ProjectLayout) -> int:
    """Count uncommitted files."""
    output = _run_git(["status", "--porcelain"], cwd=layout.root)
    return len([l for l in output.splitlines() if l.strip()])
