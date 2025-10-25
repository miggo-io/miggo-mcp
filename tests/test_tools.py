from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from miggo_public_server.config import PublicServerSettings
from miggo_public_server.tools import register_services_tools


def make_settings() -> PublicServerSettings:
    return PublicServerSettings(
        api_url="https://api-beta.miggo.io",
        token="token",
        default_take=5,
        default_skip=1,
        default_sort="risk,desc",
    )


class DummyClient:
    def __init__(self, settings, *, responses):
        self.settings = settings
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, path, params=None):
        self.calls.append((path, params))
        response = self.responses.get(path)
        if callable(response):
            return response(params)
        return response


@pytest.fixture()
def settings():
    return make_settings()


@pytest.mark.asyncio
async def test_services_list_happy(monkeypatch, settings):
    responses = {
        "/v1/services/": {
            "status": 200,
            "data": [{"id": "svc-1"}],
            "meta": {"query": {"sort": [["risk", "desc"]]}},
        }
    }
    dummy = DummyClient(settings, responses=responses)
    monkeypatch.setattr(
        "miggo_public_server.tools.MiggoPublicClient",
        lambda *_args, **_kwargs: dummy,
    )

    server = SimpleNamespace(tool=lambda: (lambda func: func))
    tools = register_services_tools(server, settings)

    result = await tools["services_list"](ids=["svc-1"], take=3)

    assert result["data"] == [{"id": "svc-1"}]
    assert dummy.calls[0][0] == "/v1/services/"
    assert dummy.calls[0][1]["where.id"] == "svc-1"
    assert dummy.calls[0][1]["take"] == "3"


@pytest.mark.asyncio
async def test_services_get_fails_when_missing(monkeypatch, settings):
    responses = {"/v1/services/": {"status": 200, "data": []}}
    dummy = DummyClient(settings, responses=responses)
    monkeypatch.setattr(
        "miggo_public_server.tools.MiggoPublicClient",
        lambda *_args, **_kwargs: dummy,
    )

    server = SimpleNamespace(tool=lambda: (lambda func: func))
    tools = register_services_tools(server, settings)

    with pytest.raises(ValueError):
        await tools["services_get"]("unknown")


@pytest.mark.asyncio
async def test_services_count(monkeypatch, settings):
    responses = {"/v1/services/count": {"data": 7}}
    dummy = DummyClient(settings, responses=responses)
    monkeypatch.setattr(
        "miggo_public_server.tools.MiggoPublicClient",
        lambda *_args, **_kwargs: dummy,
    )

    server = SimpleNamespace(tool=lambda: (lambda func: func))
    tools = register_services_tools(server, settings)

    result = await tools["services_count"](ids=["svc-1"])

    assert result["data"] == 7
    assert dummy.calls[0][0] == "/v1/services/count"
    assert dummy.calls[0][1]["where.id"] == "svc-1"


@pytest.mark.asyncio
async def test_services_facets(monkeypatch, settings):
    responses = {
        "/v1/services/facets": {
            "status": 200,
            "data": {"risk": ["low"]},
        }
    }
    dummy = DummyClient(settings, responses=responses)
    monkeypatch.setattr(
        "miggo_public_server.tools.MiggoPublicClient",
        lambda *_args, **_kwargs: dummy,
    )

    server = SimpleNamespace(tool=lambda: (lambda func: func))
    tools = register_services_tools(server, settings)

    result = await tools["services_facets"](fields=["risk"], search="svc")

    assert result["data"] == {"risk": ["low"]}
    params = dummy.calls[0][1]
    assert params["fields"] == "risk"
    assert params["search"] == "svc"


@pytest.mark.asyncio
async def test_services_list_validation(settings):
    server = SimpleNamespace(tool=lambda: (lambda func: func))
    tools = register_services_tools(server, settings)

    with pytest.raises(ValidationError):
        await tools["services_list"](take=999)
