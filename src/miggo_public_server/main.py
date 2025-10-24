"""Bootstrap entry points for the Miggo public FastMCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .config import ConfigurationError, PublicServerSettings
from .tools import register_services_tools


def build_server(settings: PublicServerSettings) -> FastMCP:
    """Construct and configure the FastMCP server instance."""
    server = FastMCP("miggo-public-services")
    register_services_tools(server, settings)
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
