#!/usr/bin/env -S uv run
"""Build Miggo Public MCP standalone binaries and MCPB bundle."""

from __future__ import annotations

import hashlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
UV_LOCK_PATH = PROJECT_ROOT / "uv.lock"
SOURCE_ROOT = PROJECT_ROOT
PYFUZE_OUTPUT = DIST_DIR / "miggo-public-mcp.com"
PLAIN_OUTPUT = DIST_DIR / "miggo-public-mcp"
WINDOWS_OUTPUT = DIST_DIR / "miggo-public-mcp.exe"
BUNDLE_NAME = "miggo-public-mcp"
BUNDLE_OUTPUT = DIST_DIR / f"{BUNDLE_NAME}.mcpb"
STAGE_DIR = PROJECT_ROOT / "build" / "mcpb_stage"


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--skip-standalone",
    is_flag=True,
    help="Skip rebuilding the Pyfuze standalone binaries.",
)
@click.option(
    "--skip-bundle",
    is_flag=True,
    help="Skip packaging the MCPB bundle.",
)
@click.option(
    "--keep-stage",
    is_flag=True,
    help=f"Leave the staging directory intact at {STAGE_DIR}.",
)
def main(skip_standalone: bool, skip_bundle: bool, keep_stage: bool) -> None:
    if skip_standalone and not PLAIN_OUTPUT.exists():
        msg = "Standalone binary not found; cannot skip standalone build."
        raise FileNotFoundError(msg)

    DIST_DIR.mkdir(exist_ok=True)

    if not skip_standalone:
        _build_standalone()
        print(
            "Standalone build complete:\n"
            f"  - {PLAIN_OUTPUT}\n"
            f"  - {WINDOWS_OUTPUT}\n"
            "SHA256 sums written alongside binaries."
        )

    if skip_bundle:
        return

    if not PLAIN_OUTPUT.exists():
        msg = "Standalone binary missing; re-run without --skip-standalone or build first."
        raise FileNotFoundError(msg)

    _build_bundle(keep_stage=keep_stage)


def _build_standalone() -> None:
    """Build the standalone binaries via Pyfuze."""
    _run_pyfuze()

    if not PYFUZE_OUTPUT.exists():
        msg = f"Expected Pyfuze output at {PYFUZE_OUTPUT}, but it was not created."
        raise FileNotFoundError(msg)

    _ensure_executable(PYFUZE_OUTPUT)

    shutil.copy2(PYFUZE_OUTPUT, PLAIN_OUTPUT)
    _ensure_executable(PLAIN_OUTPUT)
    shutil.move(PYFUZE_OUTPUT, WINDOWS_OUTPUT)

    for target in (PLAIN_OUTPUT, WINDOWS_OUTPUT):
        digest = _hash_file(target)
        _write_digest_file(target, digest)


def _build_bundle(*, keep_stage: bool) -> None:
    """Package the standalone binaries into an MCPB archive."""
    if shutil.which("npx") is None:
        raise RuntimeError("npx is required to build the MCPB bundle.")

    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True)

    shutil.copy2(PLAIN_OUTPUT, STAGE_DIR / BUNDLE_NAME)
    if WINDOWS_OUTPUT.exists():
        shutil.copy2(WINDOWS_OUTPUT, STAGE_DIR / f"{BUNDLE_NAME}.exe")

    for artifact in (
        PROJECT_ROOT / "manifest.json",
        PROJECT_ROOT / "README.md",
    ):
        shutil.copy2(artifact, STAGE_DIR / artifact.name)

    license_path = PROJECT_ROOT / "LICENSE"
    if license_path.exists():
        shutil.copy2(license_path, STAGE_DIR / license_path.name)

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
    _write_digest_file(BUNDLE_OUTPUT, digest)

    print(f"MCPB bundle created:\n  - {BUNDLE_OUTPUT}")


def _run_pyfuze() -> None:
    """Invoke Pyfuze with the standard project arguments."""
    cmd = [
        "pyfuze",
        "--debug",
        "--mode",
        "online",
        "--pyproject",
        str(PYPROJECT_PATH),
        "--uv-lock",
        str(UV_LOCK_PATH),
        "--exclude",
        "tests/",
        "--exclude",
        "build/",
        "--entry",
        "run.py",
        str(SOURCE_ROOT),
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def _ensure_executable(path: Path) -> None:
    """Ensure the given file has the executable bit set for user/group/other."""
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _hash_file(path: Path) -> str:
    """Return the SHA256 digest for a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_digest_file(path: Path, digest: str) -> None:
    target = path.with_name(f"{path.name}.sha256")
    target.write_text(f"{digest}  {path.name}\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        # Click commands are invoked without manually passing argv
        main()
    except subprocess.CalledProcessError as exc:
        print(
            f"Build step failed with exit code {exc.returncode}",
            file=sys.stderr,
        )
        raise
