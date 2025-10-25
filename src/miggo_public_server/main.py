"""Bootstrap entry points for the Miggo public FastMCP server."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .client import MiggoPublicClient
from .config import PublicServerSettings
from .tools import register_all_tools


def build_server(settings: PublicServerSettings) -> FastMCP:
    """Construct and configure the FastMCP server instance."""
    client = MiggoPublicClient(settings)

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await client.aclose()

    server = FastMCP("miggo-public-services", lifespan=lifespan)
    register_all_tools(server, settings, client)
    return server


def main() -> None:
    """Load configuration, prepare the server, and start the stdio loop."""
    server = build_server(PublicServerSettings())
    server.run()


__all__ = ["build_server", "main"]
