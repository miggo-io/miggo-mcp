"""End-to-end smoke test against the built standalone binary.

Asserts:

- initialize handshake returns the expected protocolVersion
- tools/list reports >= 25 tools including ``services_count``
- ``services_count`` returns a non-negative integer (auth + API round-trip)

Spawns the binary through a launcher that mirrors ``manifest.json``: an
inline ``bash -c`` wrapper on Unix, a temp ``.bat`` shim on Windows. The
``.bat`` indirection sidesteps Python ``subprocess.list2cmdline`` escaping
the inner double-quotes in a ``cmd /c "..."`` arg as ``\\"`` (cmd treats
``\\`` literally and the launch fails). The launcher silences Pyfuze's
first-run extraction output before invoking the real server, matching the
production launcher used by Claude Desktop.

Run locally::

    MIGGO_PUBLIC_TOKEN=... uv run pytest tests/test_smoke.py -m integration -v
"""

from __future__ import annotations

import os
import platform
import tempfile
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_PROTOCOL = "2025-06-18"
MIN_TOOLS = 25


def _launcher_params(binary: str, token: str) -> StdioServerParameters:
    abs_binary = str(Path(binary).resolve())
    env = {**os.environ, "MIGGO_PUBLIC_TOKEN": token}

    if platform.system() == "Windows":
        bat = Path(tempfile.gettempdir()) / "miggo-mcp-test-launcher.bat"
        bat.write_text(
            f'@echo off\r\n"{abs_binary}" <nul >nul 2>&1\r\n"{abs_binary}"\r\n'
        )
        return StdioServerParameters(
            command="cmd",
            args=["/c", str(bat)],
            env=env,
        )

    return StdioServerParameters(
        command="bash",
        args=[
            "-c",
            (
                f"chmod +x '{abs_binary}' 2>/dev/null; "
                f"'{abs_binary}' < /dev/null > /dev/null 2>&1; "
                f"exec '{abs_binary}'"
            ),
        ],
        env=env,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_mcp_session() -> None:
    token = os.environ.get("MIGGO_PUBLIC_TOKEN")
    if not token:
        pytest.skip("MIGGO_PUBLIC_TOKEN not set")

    binary = os.environ.get("MIGGO_MCP_BINARY", "dist/miggo-mcp")
    if not Path(binary).exists():
        pytest.skip(
            f"binary not found at {binary} — "
            "run `uv run python scripts/build.py --skip-bundle` first"
        )

    params = _launcher_params(binary, token)

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
