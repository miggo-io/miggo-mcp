import pytest

from miggo_public_mcp.query import compose_params, serialize_sort, serialize_where


def test_serialize_where_multiple_values():
    params = serialize_where({"id": ["a", "b"], "name": ["service"]})
    assert params == {"where.id": "a,b", "where.name": "service"}


def test_serialize_where_skips_none():
    params = serialize_where({"id": None, "name": []})
    assert params == {}


def test_serialize_sort_round_trip():
    sort = serialize_sort([["name", "asc"], ["risk", "desc"]])
    assert sort == "name,asc,risk,desc"


def test_serialize_sort_rejects_invalid_pair():
    with pytest.raises(
        ValueError, match="Sort tuples must contain exactly two elements"
    ):
        serialize_sort([["name"]])


def test_compose_params_full():
    params = compose_params(
        filters={"id": ["svc1"]},
        skip=5,
        take=10,
        sort=[["risk", "desc"]],
        search="api",
        fields=["name", "risk"],
        extra={"custom": "value"},
    )

    assert params["where.id"] == "svc1"
    assert params["skip"] == "5"
    assert params["take"] == "10"
    assert params["sort"] == "risk,desc"
    assert params["search"] == "api"
    assert params["fields"] == "name,risk"
    assert params["custom"] == "value"
