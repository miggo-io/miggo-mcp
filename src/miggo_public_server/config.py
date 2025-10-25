"""Environment-driven configuration for the Miggo public FastMCP server."""

from __future__ import annotations

from typing import Mapping, MutableMapping

from pydantic import Field, HttpUrl, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import MAX_PAGE_SIZE, SERVICES_FIELDS

DEFAULT_API_URL = "https://api-beta.miggo.io"
DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_OFFSET = 0
DEFAULT_SORT = "risk,desc"


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class PublicServerSettings(BaseSettings):
    """Static configuration derived from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MIGGO_PUBLIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_url: HttpUrl = Field(default=DEFAULT_API_URL, alias="api_url")
    token: str = Field(..., alias="token")
    default_take: int = Field(
        default=DEFAULT_PAGE_SIZE,
        alias="default_take",
        ge=0,
        le=MAX_PAGE_SIZE,
    )
    default_skip: int = Field(
        default=DEFAULT_PAGE_OFFSET,
        alias="default_skip",
        ge=0,
    )
    default_sort: str = Field(
        default=DEFAULT_SORT,
        alias="default_sort",
    )

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
            if field not in SERVICES_FIELDS:
                raise ValueError(f"Unsupported sort field: {field}")
            if direction not in {"asc", "desc"}:
                raise ValueError(f"Unsupported sort direction: {direction}")
            normalized.extend([field, direction])

        return ",".join(normalized)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | MutableMapping[str, str] | None = None,
    ) -> "PublicServerSettings":
        """Construct settings from environment variables or a provided mapping."""
        try:
            if env is None:
                return cls()

            data = {
                "api_url": env.get("MIGGO_PUBLIC_API_URL", env.get("api_url", DEFAULT_API_URL)),
                "token": env.get("MIGGO_PUBLIC_TOKEN") or env.get("token"),
                "default_take": env.get("MIGGO_PUBLIC_DEFAULT_TAKE", env.get("default_take", DEFAULT_PAGE_SIZE)),
                "default_skip": env.get("MIGGO_PUBLIC_DEFAULT_SKIP", env.get("default_skip", DEFAULT_PAGE_OFFSET)),
                "default_sort": env.get("MIGGO_PUBLIC_DEFAULT_SORT", env.get("default_sort", DEFAULT_SORT)),
            }
            return cls(**data)
        except ValidationError as exc:  # pragma: no cover - string formatting
            raise ConfigurationError(_format_validation_error(exc)) from exc


def _format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(segment) for segment in error.get("loc", ()))
        message = error.get("msg", "Invalid configuration value")
        parts.append(f"{loc}: {message}" if loc else message)
    return "; ".join(parts)


__all__ = [
    "ConfigurationError",
    "DEFAULT_API_URL",
    "DEFAULT_PAGE_OFFSET",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_SORT",
    "PublicServerSettings",
]
