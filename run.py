#!/usr/bin/env python3
"""Convenience entry point for running the Miggo MCP server."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import shutil
import sys
from collections.abc import Sequence

_BOOTSTRAP_SENTINEL = "MIGGO_MCP_BOOTSTRAPPED"


def _ensure_uv_bootstrap(argv: Sequence[str]) -> None:
    """Re-exec the script under `uv run --project …` if dependencies are missing."""
    if importlib.util.find_spec("pydantic") is not None:
        os.environ[_BOOTSTRAP_SENTINEL] = "1"
        return

    if os.environ.get(_BOOTSTRAP_SENTINEL) == "1":
        # We already attempted to bootstrap with uv and still cannot import pydantic.
        raise ModuleNotFoundError(
            "Required dependency 'pydantic' is not installed. Run `uv sync` or install project dependencies."
        )

    uv_executable = shutil.which("uv")
    if uv_executable is None:
        raise ModuleNotFoundError(
            "Required dependency 'pydantic' is not installed and the `uv` command was not found on PATH. "
            "Install dependencies with `uv sync` or ensure they are available in your environment."
        )

    script_path = pathlib.Path(__file__).resolve()
    project_dir = script_path.parent
    env = os.environ.copy()
    env[_BOOTSTRAP_SENTINEL] = "1"
    cmd = [
        uv_executable,
        "run",
        "--project",
        str(project_dir),
        str(script_path),
        *argv[1:],
    ]
    os.execve(uv_executable, cmd, env)  # noqa: S606 - intentional re-exec under uv


_ensure_uv_bootstrap(sys.argv)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))


# We import at the bottom since now we're absolutely sure we've been
# bootstrapped
from miggo_mcp.config import PublicServerSettings  # noqa: E402
from miggo_mcp.main import build_server  # noqa: E402

_settings = PublicServerSettings()
server = build_server(_settings)

if __name__ == "__main__":
    server.run()
