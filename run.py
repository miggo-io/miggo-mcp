#!/usr/bin/env python3
"""Convenience entry point for running the Miggo MCP server.

Claude Desktop's bundled uv (via MCPB ``"server.type": "uv"``) provisions the
environment from ``pyproject.toml`` + ``uv.lock`` and runs this file directly.
For local development, run via ``uv run run.py``.
"""

from __future__ import annotations

from miggo_mcp.config import PublicServerSettings
from miggo_mcp.main import build_server

server = build_server(PublicServerSettings())

if __name__ == "__main__":
    server.run()
