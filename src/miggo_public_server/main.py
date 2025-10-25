"""Bootstrap entry points for the Miggo public FastMCP server."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .client import MiggoPublicClient
from .config import PublicServerSettings
from .tools import register_all_tools

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    """Initialize root logging so auth debug statements are visible."""
    level_name = os.getenv("MIGGO_PUBLIC_LOG_LEVEL") or os.getenv("LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=_LOG_FORMAT)
    else:
        root_logger.setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)


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
    configure_logging()
    server = build_server(PublicServerSettings())
    server.run()


__all__ = ["build_server", "configure_logging", "main"]
