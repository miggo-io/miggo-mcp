"""Environment-driven configuration for the Miggo public FastMCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, MutableMapping


DEFAULT_API_URL = "https://api-beta.miggo.io"
DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_OFFSET = 0
DEFAULT_SORT = "risk,desc"


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class PublicServerSettings:
    """Static configuration derived from environment variables."""

    api_url: str
    token: str
    default_take: int = DEFAULT_PAGE_SIZE
    default_skip: int = DEFAULT_PAGE_OFFSET
    default_sort: str = DEFAULT_SORT

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | MutableMapping[str, str] | None = None,
    ) -> "PublicServerSettings":
        """Construct settings from environment variables."""
        source = os.environ if env is None else env

        api_url = source.get("MIGGO_PUBLIC_API_URL")
        token = source.get("MIGGO_PUBLIC_TOKEN")

        missing: list[str] = []
        if not api_url:
            missing.append("MIGGO_PUBLIC_API_URL")
        if not token:
            missing.append("MIGGO_PUBLIC_TOKEN")

        if missing:
            raise ConfigurationError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + ". Please export them before starting the server."
            )

        default_take = _parse_int(
            source.get("MIGGO_PUBLIC_DEFAULT_TAKE"),
            DEFAULT_PAGE_SIZE,
            name="MIGGO_PUBLIC_DEFAULT_TAKE",
            minimum=0,
        )
        default_skip = _parse_int(
            source.get("MIGGO_PUBLIC_DEFAULT_SKIP"),
            DEFAULT_PAGE_OFFSET,
            name="MIGGO_PUBLIC_DEFAULT_SKIP",
            minimum=0,
        )
        default_sort = source.get("MIGGO_PUBLIC_DEFAULT_SORT", DEFAULT_SORT)

        return cls(
            api_url=api_url.rstrip("/"),
            token=token,
            default_take=default_take,
            default_skip=default_skip,
            default_sort=default_sort,
        )


def _parse_int(
    raw_value: str | None,
    default: int,
    *,
    name: str,
    minimum: int | None = None,
) -> int:
    """Parse an integer environment variable with optional bounds checking."""
    if raw_value is None or raw_value == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:  # pragma: no cover - exercised in tests later
        raise ConfigurationError(
            f"{name} must be an integer value; received {raw_value!r}"
        ) from exc

    if minimum is not None and value < minimum:
        raise ConfigurationError(
            f"{name} must be >= {minimum}; received {value}"
        )

    return value


__all__ = [
    "ConfigurationError",
    "DEFAULT_API_URL",
    "DEFAULT_PAGE_OFFSET",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_SORT",
    "PublicServerSettings",
]
