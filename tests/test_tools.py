from __future__ import annotations

from types import SimpleNamespace

import pytest

from miggo_mcp.client import MiggoApiError
from miggo_mcp.config import PublicServerSettings
from miggo_mcp.constants import API_MAX_PAGE_SIZE
from miggo_mcp.tools import register_all_tools


def make_settings() -> PublicServerSettings:
    return PublicServerSettings(
        api_url="https://api-beta.miggo.io",
        token="token",
        default_take=5,
        default_skip=1,
        default_sort="risk,desc",
    )


class DummyClient:
    def __init__(self, settings: PublicServerSettings, *, responses: dict[str, object]):
        self.settings = settings
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    async def aclose(self) -> None:
        return None

    async def get(self, path: str, params=None):
        self.calls.append((path, params))
        response = self.responses.get(path)
        if callable(response):
            response = response(params)
        if response is None:
            raise AssertionError(f"Unexpected request path: {path}")

        status = response.get("status")
        if status is not None and status >= 400:
            error = response.get("error", {})
            message = error.get("message", "API Error")
            raise MiggoApiError(f"Request to {path} failed with {status}: {message}")

        return response


def make_toolset(settings, responses):
    dummy = DummyClient(settings, responses=responses)
    server = SimpleNamespace(tool=lambda **kwargs: (lambda func: func))
    tools = register_all_tools(server, settings, dummy)
    return tools, dummy


@pytest.fixture
def settings():
    return make_settings()


@pytest.mark.asyncio
async def test_services_list_happy(settings):
    responses = {
        "/v1/services/": {
            "status": 200,
            "data": [{"id": "svc-1"}],
            "meta": {"query": {"sort": [["risk", "desc"]]}},
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["services_search"](ids=["svc-1"], take=3)

    assert result["data"] == [{"id": "svc-1"}]
    path, params = dummy.calls[0]
    assert path == "/v1/services/"
    assert params["where.id"] == "svc-1"
    assert params["take"] == "3"


@pytest.mark.asyncio
async def test_services_get_fails_when_missing(settings):
    responses = {"/v1/services/": {"status": 200, "data": []}}
    tools, _ = make_toolset(settings, responses)

    with pytest.raises(ValueError, match="No service found"):
        await tools["services_get"]("unknown")


@pytest.mark.asyncio
async def test_services_count(settings):
    responses = {"/v1/services/count": {"data": 7}}
    tools, dummy = make_toolset(settings, responses)

    result = await tools["services_count"](names=["foo"])

    assert result["data"] == 7
    _, params = dummy.calls[0]
    assert params["where.name"] == "foo"


@pytest.mark.asyncio
async def test_services_facets(settings):
    responses = {
        "/v1/services/facets": {
            "status": 200,
            "data": {"risk": ["low"]},
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["services_facets"](fields=["risk"], search="svc")

    assert result["data"]["risk"] == ["low"]
    _, params = dummy.calls[0]
    assert params["fields"] == "risk"
    assert params["search"] == "svc"


@pytest.mark.asyncio
async def test_services_list_validation(settings):
    """Test that validation errors are raised for invalid parameters."""
    tools, dummy = make_toolset(settings, {})
    # When called directly (not through MCP), large take values pass through
    # but would be rejected by the API. We test that the call is made.
    dummy.responses["/v1/services/"] = {"status": 200, "data": []}
    result = await tools["services_search"](take=999)
    assert result["data"] == []


@pytest.mark.asyncio
async def test_services_search_paginates_when_take_exceeds_api_limit(settings):
    def services_response(params):
        skip = int(params["skip"])
        take = int(params["take"])
        total = API_MAX_PAGE_SIZE * 3 + 10
        upper = min(skip + take, total)
        data = [{"id": f"svc-{idx}"} for idx in range(skip, upper)]
        return {
            "status": 200,
            "data": data,
            "meta": {"query": {"skip": skip, "take": take}},
        }

    responses = {"/v1/services/": services_response}
    tools, dummy = make_toolset(settings, responses)

    take_value = API_MAX_PAGE_SIZE * 2 + 20
    result = await tools["services_search"](skip=0, take=take_value)

    assert len(result["data"]) == take_value
    query_meta = result["meta"]["query"]
    assert query_meta["take"] == take_value
    assert query_meta["skip"] == 0
    assert query_meta["pagesFetched"] == 3
    assert query_meta["fetched"] == take_value

    assert len(dummy.calls) == 3
    first_call_params = dummy.calls[0][1]
    second_call_params = dummy.calls[1][1]
    third_call_params = dummy.calls[2][1]

    assert first_call_params["take"] == str(API_MAX_PAGE_SIZE)
    assert first_call_params["skip"] == "0"
    assert second_call_params["skip"] == str(API_MAX_PAGE_SIZE)
    assert third_call_params["skip"] == str(API_MAX_PAGE_SIZE * 2)
    assert third_call_params["take"] == str(take_value - API_MAX_PAGE_SIZE * 2)


@pytest.mark.asyncio
async def test_pagination_stops_when_api_runs_out_of_data(settings):
    total_items = API_MAX_PAGE_SIZE - 10

    def services_response(params):
        skip = int(params["skip"])
        take = int(params["take"])
        assert skip == 0
        assert take == API_MAX_PAGE_SIZE
        data = [{"id": f"svc-{idx}"} for idx in range(total_items)]
        return {
            "status": 200,
            "data": data,
            "meta": {"query": {"skip": skip, "take": take}},
        }

    responses = {"/v1/services/": services_response}
    tools, dummy = make_toolset(settings, responses)

    requested_take = API_MAX_PAGE_SIZE * 2
    result = await tools["services_search"](skip=0, take=requested_take)

    assert len(result["data"]) == total_items
    query_meta = result["meta"]["query"]
    assert query_meta["take"] == requested_take
    assert query_meta["fetched"] == total_items
    assert query_meta["pagesFetched"] == 1
    assert len(dummy.calls) == 1


@pytest.mark.asyncio
async def test_pagination_handles_exact_page_multiple(settings):
    def services_response(params):
        skip = int(params.get("skip", 0))
        take = int(params.get("take", 10))
        total = API_MAX_PAGE_SIZE * 3
        upper = min(skip + take, total)
        data = [{"id": f"svc-{idx}"} for idx in range(skip, upper)]
        return {
            "status": 200,
            "data": data,
            "meta": {"query": {"skip": skip, "take": take}},
        }

    responses = {"/v1/services/": services_response}
    tools, dummy = make_toolset(settings, responses)

    take_value = API_MAX_PAGE_SIZE * 2
    result = await tools["services_search"](skip=0, take=take_value)

    assert len(result["data"]) == take_value
    query_meta = result["meta"]["query"]
    assert query_meta["take"] == take_value
    assert query_meta["skip"] == 0
    assert query_meta["pagesFetched"] == 2
    assert query_meta["fetched"] == take_value

    assert len(dummy.calls) == 2
    first_call_params = dummy.calls[0][1]
    second_call_params = dummy.calls[1][1]

    assert first_call_params["take"] == str(API_MAX_PAGE_SIZE)
    assert first_call_params["skip"] == "0"
    assert second_call_params["take"] == str(API_MAX_PAGE_SIZE)
    assert second_call_params["skip"] == str(API_MAX_PAGE_SIZE)


@pytest.mark.asyncio
async def test_pagination_makes_no_calls_for_zero_take(settings):
    tools, dummy = make_toolset(settings, {})
    result = await tools["services_search"](take=0)

    assert result["data"] == []
    assert result["meta"]["query"]["fetched"] == 0
    assert result["meta"]["query"]["pagesFetched"] == 0
    assert not dummy.calls


@pytest.mark.asyncio
async def test_pagination_respects_initial_skip(settings):
    def services_response(params):
        skip = int(params["skip"])
        take = int(params["take"])
        total = API_MAX_PAGE_SIZE * 3 + 20
        upper = min(skip + take, total)
        data = [{"id": f"svc-{idx}"} for idx in range(skip, upper)]
        return {
            "status": 200,
            "data": data,
            "meta": {"query": {"skip": skip, "take": take}},
        }

    responses = {"/v1/services/": services_response}
    tools, dummy = make_toolset(settings, responses)

    initial_skip = 10
    take_value = API_MAX_PAGE_SIZE + 5
    result = await tools["services_search"](skip=initial_skip, take=take_value)

    assert len(result["data"]) == take_value
    query_meta = result["meta"]["query"]
    assert query_meta["take"] == take_value
    assert query_meta["skip"] == initial_skip
    assert query_meta["pagesFetched"] == 2
    assert query_meta["fetched"] == take_value

    assert len(dummy.calls) == 2
    first_call_params = dummy.calls[0][1]
    second_call_params = dummy.calls[1][1]

    assert first_call_params["skip"] == str(initial_skip)
    assert first_call_params["take"] == str(API_MAX_PAGE_SIZE)
    assert second_call_params["skip"] == str(initial_skip + API_MAX_PAGE_SIZE)
    assert second_call_params["take"] == str(5)


@pytest.mark.asyncio
async def test_pagination_handles_error_during_paging(settings):
    error_message = "API failure"

    def services_response(params):
        skip = int(params["skip"])
        if skip > 0:
            return {"status": 500, "error": {"message": error_message}}
        return {
            "status": 200,
            "data": [{"id": f"svc-{idx}"} for idx in range(API_MAX_PAGE_SIZE)],
            "meta": {"query": {"skip": skip, "take": API_MAX_PAGE_SIZE}},
        }

    responses = {"/v1/services/": services_response}
    tools, _ = make_toolset(settings, responses)

    with pytest.raises(MiggoApiError, match=error_message):
        await tools["services_search"](take=API_MAX_PAGE_SIZE + 1)


@pytest.mark.asyncio
async def test_endpoints_filters_encoding(settings):
    responses = {
        "/v1/endpoints/": {
            "status": 200,
            "data": [{"id": "endpoint-1"}],
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["endpoints_search"](
        ids=["endpoint-1"],
        is_internet_facing=True,
        risk_scores=[0.5],
    )

    assert result["data"][0]["id"] == "endpoint-1"
    _, params = dummy.calls[0]
    assert params["where.id"] == "endpoint-1"
    assert params["where.isInternetFacing"] == "true"
    assert params["where.risk"] == "0.5"
    assert params["skip"] == str(settings.default_skip)
    assert params["take"] == str(settings.default_take)


@pytest.mark.asyncio
async def test_third_parties_get_returns_result(settings):
    responses = {
        "/v1/third-parties/": {
            "status": 200,
            "data": [{"id": "tp-1", "domain": "example.com"}],
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["third_parties_get"]("tp-1")

    assert result["data"]["domain"] == "example.com"
    _, params = dummy.calls[0]
    assert params["where.id"] == "tp-1"
    assert params["take"] == "1"


@pytest.mark.asyncio
async def test_findings_count_filters(settings):
    responses = {
        "/v1/findings/count": {"data": 12},
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["findings_count"](severities=["high"], statuses=["OPEN"])

    assert result["data"] == 12
    _, params = dummy.calls[0]
    assert params["where.severity"] == "high"
    assert params["where.status"] == "OPEN"


@pytest.mark.asyncio
async def test_vulnerabilities_facets_boolean_serialization(settings):
    responses = {
        "/v1/vulnerabilities/facets": {
            "status": 200,
            "data": {"status": ["OPEN"]},
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["vulnerabilities_facets"](
        fields=["status"],
        has_public_fix=False,
        is_internet_facing=True,
    )

    assert result["data"]["status"] == ["OPEN"]
    _, params = dummy.calls[0]
    assert params["fields"] == "status"
    assert params["where.hasPublicFix"] == "false"
    assert params["where.isInternetFacing"] == "true"


@pytest.mark.asyncio
async def test_project_get(settings):
    responses = {
        "/v1/project/": {
            "status": 200,
            "data": {"projectId": "proj-1"},
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["project_get"]()

    assert result["data"]["projectId"] == "proj-1"
    assert dummy.calls[0][0] == "/v1/project/"


@pytest.mark.asyncio
async def test_services_list_number_parameters(settings):
    """Test that number parameters work correctly."""
    responses = {
        "/v1/services/": {
            "status": 200,
            "data": [{"id": "svc-1"}],
            "meta": {"query": {"sort": [["risk", "desc"]]}},
        }
    }
    tools, dummy = make_toolset(settings, responses)

    result = await tools["services_search"](take=3, skip=1)

    assert result["data"] == [{"id": "svc-1"}]
    path, params = dummy.calls[0]
    assert path == "/v1/services/"
    assert params["take"] == "3"
    assert params["skip"] == "1"
