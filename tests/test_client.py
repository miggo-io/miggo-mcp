import pytest

from miggo_mcp.client import MiggoApiError, MiggoPublicClient
from miggo_mcp.config import (
    DEFAULT_ACCESS_KEY_EXCHANGE_URL,
    DEFAULT_ACCESS_KEY_ID,
    PublicServerSettings,
)


def make_settings() -> PublicServerSettings:
    return PublicServerSettings(
        api_url="https://api-beta.miggo.io",
        token="api-key",
        default_take=10,
        default_skip=0,
        default_sort="risk,desc",
    )


@pytest.mark.asyncio
async def test_client_get_success(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=DEFAULT_ACCESS_KEY_EXCHANGE_URL,
        match_headers={
            "Authorization": f"Bearer {DEFAULT_ACCESS_KEY_ID}:api-key",
        },
        json={"sessionJwt": "jwt-token", "sessionExpiresAt": "2099-01-01T00:00:00Z"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
        match_headers={"Authorization": "Bearer jwt-token"},
        json={"status": 200, "data": []},
    )

    settings = make_settings()
    async with MiggoPublicClient(settings) as client:
        payload = await client.get("/v1/services/")

    assert payload["status"] == 200
    assert payload["data"] == []


@pytest.mark.asyncio
async def test_client_get_error(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=DEFAULT_ACCESS_KEY_EXCHANGE_URL,
        json={"sessionJwt": "jwt-token"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
        status_code=500,
        json={"message": "boom"},
    )

    settings = make_settings()
    async with MiggoPublicClient(settings) as client:
        with pytest.raises(MiggoApiError):
            await client.get("/v1/services/")


@pytest.mark.asyncio
async def test_client_refreshes_jwt_on_unauthorized(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=DEFAULT_ACCESS_KEY_EXCHANGE_URL,
        json={"sessionJwt": "first-jwt"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
        status_code=401,
        json={"message": "unauthorized"},
    )
    httpx_mock.add_response(
        method="POST",
        url=DEFAULT_ACCESS_KEY_EXCHANGE_URL,
        json={"sessionJwt": "second-jwt"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
        match_headers={"Authorization": "Bearer second-jwt"},
        json={"status": 200, "data": []},
    )

    settings = make_settings()
    async with MiggoPublicClient(settings) as client:
        payload = await client.get("/v1/services/")

    assert payload["status"] == 200
    assert payload["data"] == []


@pytest.mark.asyncio
async def test_client_exchange_failure_raises(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=DEFAULT_ACCESS_KEY_EXCHANGE_URL,
        status_code=500,
        json={"message": "nope"},
    )

    settings = make_settings()
    async with MiggoPublicClient(settings) as client:
        with pytest.raises(MiggoApiError):
            await client.get("/v1/services/")
