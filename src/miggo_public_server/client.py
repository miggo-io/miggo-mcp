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
_MASK_PREFIX = 4
_MASK_SUFFIX = 4


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
        self._default_headers = {"Accept": "application/json"}
        api_base_url = str(settings.api_url)
        if client is None:
            self._client = httpx.AsyncClient(
                base_url=api_base_url,
                timeout=timeout,
                headers=self._default_headers.copy(),
            )
        else:
            self._client = client
            if self._client.headers.get("accept") is None:
                self._client.headers.update(self._default_headers)
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
        headers = self._build_request_headers(jwt)
        logger.debug(
            "Dispatching %s %s with session jwt=%s",
            method,
            path,
            _mask_token(jwt),
        )
        response = await self._client.request(
            method,
            path,
            params=params,
            headers=headers,
        )
        logger.debug(
            "Received %s response for %s %s",
            response.status_code,
            method,
            path,
        )
        if response.status_code == 401:
            logger.info(
                "Miggo API returned 401 for %s %s using jwt=%s; refreshing",
                method,
                path,
                _mask_token(jwt),
            )
            jwt = await self._ensure_session_jwt(force_refresh=True)
            headers = self._build_request_headers(jwt)
            response = await self._client.request(
                method,
                path,
                params=params,
                headers=headers,
            )
            logger.debug(
                "Retry received %s response for %s %s",
                response.status_code,
                method,
                path,
            )
        return response

    async def _ensure_session_jwt(self, *, force_refresh: bool = False) -> str:
        if not force_refresh and self._is_session_valid():
            assert self._session_jwt is not None
            logger.debug(
                "Using cached session jwt=%s (expires_at=%s)",
                _mask_token(self._session_jwt),
                self._session_expires_at.isoformat()
                if isinstance(self._session_expires_at, datetime)
                else "unknown",
            )
            return self._session_jwt

        async with self._jwt_lock:
            if not force_refresh and self._is_session_valid():
                assert self._session_jwt is not None
                logger.debug(
                    "Using cached session jwt=%s (expires_at=%s) after lock",
                    _mask_token(self._session_jwt),
                    self._session_expires_at.isoformat()
                    if isinstance(self._session_expires_at, datetime)
                    else "unknown",
                )
                return self._session_jwt

            logger.info(
                "Exchanging API key for session JWT (force_refresh=%s)",
                force_refresh,
            )
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
        logger.info("Requesting session JWT via %s", exchange_url)
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
        if isinstance(expires_at, datetime):
            remaining = expires_at - datetime.now(UTC)
            logger.info(
                "Obtained session jwt=%s (valid for ~%s)",
                _mask_token(session_jwt),
                remaining,
            )
        else:
            logger.info("Obtained session jwt=%s (no explicit expiry)", _mask_token(session_jwt))
        logger.debug(
            "Obtained session JWT (expires at %s)",
            expires_at.isoformat() if isinstance(expires_at, datetime) else "unknown",
        )
        return session_jwt, expires_at

    def _build_request_headers(self, jwt: str) -> dict[str, str]:
        headers = self._default_headers.copy()
        headers["Authorization"] = f"Bearer {jwt}"
        return headers


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


def _mask_token(token: str | None) -> str:
    if not token:
        return "unknown"
    if len(token) <= _MASK_PREFIX + _MASK_SUFFIX:
        return f"{token[:_MASK_PREFIX]}***"
    return f"{token[:_MASK_PREFIX]}...{token[-_MASK_SUFFIX:]}"


__all__ = ["MiggoApiError", "MiggoPublicClient"]
