"""Shared constants and type aliases for the Miggo public FastMCP server."""

from __future__ import annotations

from typing import Literal

ServiceField = Literal[
    "id",
    "name",
    "isInternetFacing",
    "isThirdPartyCommunication",
    "isAuthenticated",
    "createdAt",
    "updatedAt",
    "technology",
    "lastAccessed",
    "risk",
]

SortDirection = Literal["asc", "desc"]

SERVICES_FIELDS = [
    "id",
    "name",
    "isInternetFacing",
    "isThirdPartyCommunication",
    "isAuthenticated",
    "createdAt",
    "updatedAt",
    "technology",
    "lastAccessed",
    "risk",
]

MAX_PAGE_SIZE = 50

__all__ = ["MAX_PAGE_SIZE", "SERVICES_FIELDS", "ServiceField", "SortDirection"]
