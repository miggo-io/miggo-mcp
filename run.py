#!/usr/bin/env python3
"""Convenience entry point for running the Miggo MCP server.

Claude Desktop's bundled uv (via MCPB ``"server.type": "uv"``) provisions the
environment from ``pyproject.toml`` + ``uv.lock`` and runs this file directly.
The ``sys.path`` shim below lets the script also run with ``./run.py`` or
``python /path/to/run.py`` from any working directory without first installing
the project — useful for ad-hoc testing.
"""

from __future__ import annotations

import pathlib
import sys

_SRC_DIR = pathlib.Path(__file__).resolve().parent / "src"
if _SRC_DIR.is_dir() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from miggo_mcp.config import PublicServerSettings  # noqa: E402
from miggo_mcp.main import build_server  # noqa: E402

server = build_server(PublicServerSettings())

if __name__ == "__main__":
    server.run()
