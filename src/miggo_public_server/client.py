"""Async client wrapper around Miggo's public API."""

from __future__ import annotations

import logging
from typing import Any, Mapping, MutableMapping

import httpx

from .config import PublicServerSettings

logger = logging.getLogger(__name__)


class MiggoApiError(RuntimeError):
    """Raised when Miggo's API returns an error response."""


class MiggoPublicClient:
    """Thin convenience wrapper over ``httpx.AsyncClient``."""

    def __init__(
        self,
        settings: PublicServerSettings,
        *,
        timeout: float | httpx.Timeout | None = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=settings.api_url,
            timeout=timeout,
            headers=self._build_headers(settings),
        )
        self._owns_client = client is None

    async def __aenter__(self) -> "MiggoPublicClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    @property
    def settings(self) -> PublicServerSettings:
        return self._settings

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> MutableMapping[str, Any]:
        """Issue a GET request and decode the JSON response."""
        logger.debug("GET %s params=%s", path, params)
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Miggo API responded with %s for %s",
                exc.response.status_code,
                path,
                exc_info=True,
            )
            body = _safe_json(exc.response)
            message = body.get("message") if isinstance(body, Mapping) else None
            raise MiggoApiError(
                f"Request to {path!s} failed with {exc.response.status_code}: {message or exc}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Miggo API request to %s failed: %s", path, exc, exc_info=True)
            raise MiggoApiError(f"Request to {path!s} failed: {exc}") from exc

        json_body = _safe_json(response)
        if not isinstance(json_body, MutableMapping):
            raise MiggoApiError("Unexpected response payload (expected JSON object)")
        return json_body

    @staticmethod
    def _build_headers(settings: PublicServerSettings) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.token}",
            "Accept": "application/json",
        }


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        logger.debug("Failed to decode JSON for response %s", response.text)
        return {}


__all__ = ["MiggoApiError", "MiggoPublicClient"]
