"""Tool registration helpers for the Miggo public FastMCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..config import PublicServerSettings


def register_services_tools(server: FastMCP, settings: PublicServerSettings) -> None:
    """Register placeholder tool definitions for the services API."""

    @server.tool()
    async def services_list(**_kwargs):
        """List services from Miggo's public API."""
        raise NotImplementedError("services_list will be implemented in Step 5")

    @server.tool()
    async def services_count(**_kwargs):
        """Return the count of services from Miggo's public API."""
        raise NotImplementedError("services_count will be implemented in Step 5")

    @server.tool()
    async def services_facets(**_kwargs):
        """Fetch available facet values across services."""
        raise NotImplementedError("services_facets will be implemented in Step 5")


__all__ = ["register_services_tools"]
