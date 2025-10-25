"""Async client wrapper around Miggo's public API."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping, MutableMapping

import httpx

from .config import PublicServerSettings

logger = logging.getLogger(__name__)

_JWT_REFRESH_SKEW = timedelta(seconds=30)


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
        default_headers = {"Accept": "application/json"}
        if client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.api_url,
                timeout=timeout,
                headers=default_headers,
            )
        else:
            self._client = client
            if self._client.headers.get("accept") is None:
                self._client.headers.update(default_headers)
        self._owns_client = client is None
        self._session_jwt: str | None = None
        self._session_expires_at: datetime | None = None
        self._jwt_lock = asyncio.Lock()

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
            response = await self._authorized_request(
                "GET",
                path,
                params=params,
            )
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

    async def _authorized_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        jwt = await self._ensure_session_jwt()
        headers = {"Authorization": f"Bearer {jwt}"}
        response = await self._client.request(
            method,
            path,
            params=params,
            headers=headers,
        )
        if response.status_code == 401:
            logger.info("Miggo API returned 401, refreshing session JWT")
            jwt = await self._ensure_session_jwt(force_refresh=True)
            headers = {"Authorization": f"Bearer {jwt}"}
            response = await self._client.request(
                method,
                path,
                params=params,
                headers=headers,
            )
        return response

    async def _ensure_session_jwt(self, *, force_refresh: bool = False) -> str:
        if not force_refresh and self._is_session_valid():
            assert self._session_jwt is not None
            return self._session_jwt

        async with self._jwt_lock:
            if not force_refresh and self._is_session_valid():
                assert self._session_jwt is not None
                return self._session_jwt

            jwt, expires_at = await self._exchange_for_session_jwt()
            self._session_jwt = jwt
            self._session_expires_at = expires_at
            return jwt

    def _is_session_valid(self) -> bool:
        if not self._session_jwt:
            return False
        if self._session_expires_at is None:
            return True
        now = datetime.now(UTC)
        return now + _JWT_REFRESH_SKEW < self._session_expires_at

    async def _exchange_for_session_jwt(self) -> tuple[str, datetime | None]:
        headers = {
            "Authorization": (
                f"Bearer {self._settings.access_key_id}:{self._settings.token}"
            ),
            "Accept": "application/json",
        }
        exchange_url = str(self._settings.access_key_exchange_url)
        try:
            response = await self._client.post(
                exchange_url,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Auth exchange failed with %s",
                exc.response.status_code,
                exc_info=True,
            )
            body = _safe_json(exc.response)
            message = body.get("message") if isinstance(body, Mapping) else None
            raise MiggoApiError(
                f"Authentication exchange failed with "
                f"{exc.response.status_code}: {message or exc}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Auth exchange request failed: %s", exc, exc_info=True)
            raise MiggoApiError(f"Authentication exchange failed: {exc}") from exc

        payload = _safe_json(response)
        if not isinstance(payload, Mapping):
            raise MiggoApiError("Authentication exchange returned unexpected payload")

        session_jwt = payload.get("sessionJwt")
        if not isinstance(session_jwt, str) or not session_jwt:
            raise MiggoApiError("Authentication exchange response missing sessionJwt")

        expires_at = _parse_expires_at(payload)
        logger.debug(
            "Obtained session JWT (expires at %s)",
            expires_at.isoformat() if isinstance(expires_at, datetime) else "unknown",
        )
        return session_jwt, expires_at


def _parse_expires_at(payload: Mapping[str, Any]) -> datetime | None:
    candidates = (
        "sessionExpiresAt",
        "sessionExpiration",
        "expiresAt",
        "sessionExpires",
    )
    for key in candidates:
        value = payload.get(key)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC)
            except ValueError:
                continue
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, tz=UTC)
            except (OSError, ValueError):
                continue
    return None


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        logger.debug("Failed to decode JSON for response %s", response.text)
        return {}


__all__ = ["MiggoApiError", "MiggoPublicClient"]
