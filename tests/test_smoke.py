"""End-to-end smoke test for the Miggo MCP server.

Mirrors what Claude Desktop does post-install when a ``.mcpb`` with
``"server.type": "uv"`` is loaded: invoke ``uv run --directory <project> run.py``
and exchange JSON-RPC over stdio. Asserts:

- initialize handshake returns the expected protocolVersion
- tools/list reports >= 25 tools including ``services_count``
- ``services_count`` returns a non-negative integer (auth + API round-trip)

Run locally::

    MIGGO_PUBLIC_TOKEN=... uv run pytest tests/test_smoke.py -m integration -v
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_PROTOCOL = "2025-06-18"
MIN_TOOLS = 25


def _launcher_params(token: str) -> StdioServerParameters:
    project_dir = Path(__file__).resolve().parent.parent
    return StdioServerParameters(
        command="uv",
        args=["run", "--directory", str(project_dir), "run.py"],
        env={**os.environ, "MIGGO_PUBLIC_TOKEN": token},
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_mcp_session() -> None:
    token = os.environ.get("MIGGO_PUBLIC_TOKEN")
    if not token:
        pytest.skip("MIGGO_PUBLIC_TOKEN not set")

    if shutil.which("uv") is None:
        pytest.skip("`uv` not on PATH — install via https://astral.sh/uv")

    params = _launcher_params(token)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.protocolVersion == EXPECTED_PROTOCOL

            tools_resp = await session.list_tools()
            tool_names = {t.name for t in tools_resp.tools}
            assert len(tools_resp.tools) >= MIN_TOOLS, (
                f"expected >= {MIN_TOOLS} tools, got {len(tools_resp.tools)}"
            )
            assert "services_count" in tool_names, (
                f"services_count missing from tool list ({sorted(tool_names)})"
            )

            result = await session.call_tool("services_count", {})
            assert not result.isError, f"services_count returned tool error: {result}"
            structured = result.structuredContent or {}
            data = structured.get("data")
            assert isinstance(data, int), (
                f"services_count returned {data!r}, expected int"
            )
            assert data >= 0, f"services_count returned negative {data}"
