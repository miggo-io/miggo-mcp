"""Bootstrap entry points for the Miggo public FastMCP server."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .client import MiggoPublicClient
from .config import ConfigurationError, PublicServerSettings
from .tools import register_services_tools


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
    register_services_tools(server, settings, client)
    return server


def main() -> None:
    """Load configuration, prepare the server, and start the stdio loop."""
    try:
        settings = PublicServerSettings.from_env()
    except ConfigurationError as exc:  # pragma: no cover - defensive guard
        raise SystemExit(str(exc)) from exc

    server = build_server(settings)
    server.run()


__all__ = ["build_server", "main"]
