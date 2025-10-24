"""Entry points for the Miggo public FastMCP server."""

from __future__ import annotations

import asyncio


async def run() -> None:
    """Placeholder bootstrap to be implemented in later steps."""
    raise NotImplementedError("Bootstrap will be implemented in Step 3 of plan.md")


def main() -> None:
    """Synchronous entry point for console scripts."""
    asyncio.run(run())


__all__ = ["main", "run"]
