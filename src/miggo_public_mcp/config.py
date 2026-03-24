"""Environment-driven configuration for the Miggo public FastMCP server."""

from __future__ import annotations

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import ALL_SORT_FIELDS, MAX_PAGE_SIZE

DEFAULT_API_URL = "https://api-beta.miggo.io"
DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_OFFSET = 0
DEFAULT_SORT = "risk,desc"
DEFAULT_ACCESS_KEY_EXCHANGE_URL = "https://auth.miggo.io/v1/auth/accesskey/exchange"
# This is a non-secret public client identifier used in the access-key
# exchange flow — analogous to an OAuth client_id. It is safe to embed here.
DEFAULT_ACCESS_KEY_ID = "P2UjsJwOFdIeUAtW0pGTJ5SeJAlq"


class PublicServerSettings(BaseSettings):
    """Static configuration derived from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MIGGO_PUBLIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    token: str
    api_url: HttpUrl = Field(default=DEFAULT_API_URL)
    access_key_exchange_url: HttpUrl = Field(default=DEFAULT_ACCESS_KEY_EXCHANGE_URL)
    access_key_id: str = Field(default=DEFAULT_ACCESS_KEY_ID)
    default_take: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=0,
        le=MAX_PAGE_SIZE,
    )
    default_skip: int = Field(
        default=DEFAULT_PAGE_OFFSET,
        ge=0,
    )
    default_sort: str = Field(default=DEFAULT_SORT)

    @field_validator("api_url", mode="after")
    @classmethod
    def strip_trailing_slash(cls, value: HttpUrl) -> str:
        """Normalize the API base URL by removing any trailing slash."""
        return str(value).rstrip("/")

    @field_validator("default_sort")
    @classmethod
    def normalize_default_sort(cls, value: str) -> str:
        """Ensure the default sort string uses valid field/direction pairs."""
        if not value:
            return value

        parts = [part.strip() for part in value.split(",") if part.strip()]
        if len(parts) % 2 != 0:
            raise ValueError("default_sort must provide field,direction pairs")

        normalized: list[str] = []
        for idx in range(0, len(parts), 2):
            field = parts[idx]
            direction = parts[idx + 1].lower()
            if field not in ALL_SORT_FIELDS:
                raise ValueError(f"Unsupported sort field: {field}")
            if direction not in {"asc", "desc"}:
                raise ValueError(f"Unsupported sort direction: {direction}")
            normalized.extend([field, direction])

        return ",".join(normalized)


__all__ = [
    "DEFAULT_API_URL",
    "DEFAULT_ACCESS_KEY_EXCHANGE_URL",
    "DEFAULT_ACCESS_KEY_ID",
    "DEFAULT_PAGE_OFFSET",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_SORT",
    "PublicServerSettings",
]
