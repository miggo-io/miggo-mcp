#!/usr/bin/env -S uv run
"""Build the Miggo MCP MCPB bundle.

The bundle uses MCPB ``"server.type": "uv"``: Claude Desktop's bundled uv
provisions the Python runtime from ``pyproject.toml`` + ``uv.lock`` on the
target machine, so we ship source rather than a pre-built binary.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
STAGE_DIR = PROJECT_ROOT / "build" / "mcpb_stage"
BUNDLE_OUTPUT = DIST_DIR / "miggo-mcp.mcpb"

# Files copied verbatim from the repo root into the staged bundle.
ROOT_FILES = (
    "manifest.json",
    "pyproject.toml",
    "uv.lock",
    "run.py",
    "README.md",
    "LICENSE",
    "icon.png",
)

# Patterns excluded when copying ``src/`` into the staged bundle.
SRC_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")

MCPBIGNORE = """\
.venv/
__pycache__/
*.pyc
.pytest_cache/
tests/
"""


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--keep-stage",
    is_flag=True,
    help=f"Leave the staging directory intact at {STAGE_DIR}.",
)
def main(keep_stage: bool) -> None:
    if shutil.which("npx") is None:
        raise RuntimeError("npx is required to build the MCPB bundle.")

    DIST_DIR.mkdir(exist_ok=True)
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True)

    for name in ROOT_FILES:
        src = PROJECT_ROOT / name
        if not src.exists():
            raise FileNotFoundError(f"Required file missing: {src}")
        shutil.copy2(src, STAGE_DIR / name)

    shutil.copytree(PROJECT_ROOT / "src", STAGE_DIR / "src", ignore=SRC_IGNORE)

    (STAGE_DIR / ".mcpbignore").write_text(MCPBIGNORE, encoding="utf-8")

    subprocess.run(
        ["npx", "@anthropic-ai/mcpb", "validate", "manifest.json"],
        cwd=STAGE_DIR,
        check=True,
    )
    subprocess.run(
        ["npx", "@anthropic-ai/mcpb", "pack", ".", str(BUNDLE_OUTPUT)],
        cwd=STAGE_DIR,
        check=True,
    )

    if not keep_stage:
        shutil.rmtree(STAGE_DIR)

    digest = _hash_file(BUNDLE_OUTPUT)
    BUNDLE_OUTPUT.with_name(f"{BUNDLE_OUTPUT.name}.sha256").write_text(
        f"{digest}  {BUNDLE_OUTPUT.name}\n",
        encoding="utf-8",
    )
    print(f"MCPB bundle created:\n  - {BUNDLE_OUTPUT}")


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Build step failed with exit code {exc.returncode}", file=sys.stderr)
        raise
