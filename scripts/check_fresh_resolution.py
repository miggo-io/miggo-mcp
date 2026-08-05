"""Guard against upstream breakage that `uv.lock` hides.

`uv sync` (CI, local dev) pins every dependency via `uv.lock`. The way users
actually install us — `uvx --from git+https://github.com/miggo-io/miggo-mcp
miggo-mcp` — ignores the lockfile and resolves dependencies fresh from
`pyproject.toml`. Those two paths can disagree, and when they do the break
lands on users instead of CI.

That is exactly how mcp 2.0.0 broke 0.8.1: `mcp[cli]>=1.19.0` had no upper
bound, mcp 2.0.0 removed `mcp.server.fastmcp`, and every fresh install died at
import with `ModuleNotFoundError`.

This script builds the server against a *freshly resolved* dependency set, so a
future upstream major that breaks us fails CI first. Registering the tools (not
just importing the module) means signature-level API drift is caught too, not
only outright module removal.

Run it the way CI does — the flags are the point, they bypass `uv.lock`::

    uv run --isolated --no-project --refresh --resolution highest --with . \
        python scripts/check_fresh_resolution.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from importlib import metadata

# Matches tests/test_smoke.py — assert a floor, not the exact count, so adding
# tools doesn't require touching this guard.
MIN_TOOLS = 25


def main() -> int:
    # build_server() constructs the API client but makes no network calls, so a
    # placeholder satisfies settings validation without needing a real secret.
    os.environ.setdefault("MIGGO_PUBLIC_TOKEN", "fresh-resolution-check")

    from miggo_mcp.config import PublicServerSettings
    from miggo_mcp.main import build_server

    server = build_server(PublicServerSettings())
    tools = asyncio.run(server.list_tools())

    if len(tools) < MIN_TOOLS:
        print(
            f"FAIL: registered {len(tools)} tools, expected >= {MIN_TOOLS}",
            file=sys.stderr,
        )
        return 1

    # The resolved version is the whole point of this job — log it so a CI
    # failure shows which upstream release broke us.
    print(
        f"OK: built server with {len(tools)} tools "
        f"against mcp {metadata.version('mcp')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
