import pytest
from httpx import Response

from miggo_public_server.client import MiggoApiError, MiggoPublicClient
from miggo_public_server.config import PublicServerSettings


def make_settings() -> PublicServerSettings:
    return PublicServerSettings(
        api_url="https://api-beta.miggo.io",
        token="token",
        default_take=10,
        default_skip=0,
        default_sort="risk,desc",
    )


@pytest.mark.asyncio
async def test_client_get_success(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
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
        method="GET",
        url="https://api-beta.miggo.io/v1/services/",
        status_code=500,
        json={"message": "boom"},
    )

    settings = make_settings()
    async with MiggoPublicClient(settings) as client:
        with pytest.raises(MiggoApiError):
            await client.get("/v1/services/")
