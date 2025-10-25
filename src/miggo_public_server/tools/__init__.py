"""Static MCP tool definitions for Miggo's public services API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Mapping, MutableMapping, Sequence

from mcp.server.fastmcp import FastMCP
from pydantic import Field, validate_call

from ..client import MiggoPublicClient
from ..config import PublicServerSettings
from ..constants import MAX_PAGE_SIZE, ServiceField, SortDirection
from ..query import compose_params
from ..response import collection_response, scalar_response


def register_services_tools(
    server: FastMCP, settings: PublicServerSettings
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register the static set of tools exposed by this package."""

    @server.tool()
    @validate_call
    async def services_list(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        created_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        updated_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        last_accessed: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        skip: Annotated[int | None, Field(ge=0)] = None,
        take: Annotated[int | None, Field(ge=0, le=MAX_PAGE_SIZE)] = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List Miggo services with optional filtering, sorting, and pagination."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_filters(
            ids=ids,
            names=names,
            is_internet_facing=is_internet_facing,
            is_third_party_communication=is_third_party_communication,
            is_authenticated=is_authenticated,
            technologies=technologies,
            risks=risks,
            created_at=created_at,
            updated_at=updated_at,
            last_accessed=last_accessed,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, settings),
        )

        async with MiggoPublicClient(settings) as client:
            payload = await client.get("/v1/services/", params=params)
        return collection_response(payload)

    @server.tool()
    @validate_call
    async def services_get(
        service_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a single Miggo service by identifier."""
        params = compose_params(
            filters={"id": [service_id]},
            take=1,
            sort=_resolve_sort(None, settings),
        )

        async with MiggoPublicClient(settings) as client:
            payload = await client.get("/v1/services/", params=params)

        services = payload.get("data") or []
        if not services:
            raise ValueError(f"No service found for id {service_id!r}")

        response = {"data": services[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    @server.tool()
    @validate_call
    async def services_count(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        created_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        updated_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        last_accessed: Sequence[Annotated[int, Field(ge=0)]] | None = None,
    ) -> MutableMapping[str, object]:
        """Return a count of services matching the provided filters."""
        filters = _build_filters(
            ids=ids,
            names=names,
            is_internet_facing=is_internet_facing,
            is_third_party_communication=is_third_party_communication,
            is_authenticated=is_authenticated,
            technologies=technologies,
            risks=risks,
            created_at=created_at,
            updated_at=updated_at,
            last_accessed=last_accessed,
        )

        params = compose_params(filters=filters)

        async with MiggoPublicClient(settings) as client:
            payload = await client.get("/v1/services/count", params=params)

        return scalar_response(payload)

    @server.tool()
    @validate_call
    async def services_facets(
        *,
        fields: Sequence[ServiceField] | None = None,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        created_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        updated_at: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        last_accessed: Sequence[Annotated[int, Field(ge=0)]] | None = None,
        skip: Annotated[int | None, Field(ge=0)] = None,
        take: Annotated[int | None, Field(ge=0, le=MAX_PAGE_SIZE)] = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets (distinct field values) for the services dataset."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_filters(
            ids=ids,
            names=names,
            is_internet_facing=is_internet_facing,
            is_third_party_communication=is_third_party_communication,
            is_authenticated=is_authenticated,
            technologies=technologies,
            risks=risks,
            created_at=created_at,
            updated_at=updated_at,
            last_accessed=last_accessed,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, settings),
            search=search,
        )

        async with MiggoPublicClient(settings) as client:
            payload = await client.get("/v1/services/facets", params=params)
        return collection_response(payload)

    return {
        "services_list": services_list,
        "services_get": services_get,
        "services_count": services_count,
        "services_facets": services_facets,
    }


def _build_filters(
    *,
    ids: Sequence[str] | None,
    names: Sequence[str] | None,
    is_internet_facing: bool | None,
    is_third_party_communication: bool | None,
    is_authenticated: bool | None,
    technologies: Sequence[str] | None,
    risks: Sequence[str] | None,
    created_at: Sequence[int] | None,
    updated_at: Sequence[int] | None,
    last_accessed: Sequence[int] | None,
) -> dict[str, list[object]]:
    """Translate tool arguments into Miggo ``where`` filters."""
    sequence_filters = {
        "id": _normalize_sequence(ids),
        "name": _normalize_sequence(names),
        "technology": _normalize_sequence(technologies),
        "risk": _normalize_sequence(risks),
        "createdAt": _normalize_sequence(created_at),
        "updatedAt": _normalize_sequence(updated_at),
        "lastAccessed": _normalize_sequence(last_accessed),
    }

    boolean_filters = {
        "isInternetFacing": [is_internet_facing] if is_internet_facing is not None else None,
        "isThirdPartyCommunication": (
            [is_third_party_communication] if is_third_party_communication is not None else None
        ),
        "isAuthenticated": [is_authenticated] if is_authenticated is not None else None,
    }

    combined = {
        field: values
        for field, values in {**sequence_filters, **boolean_filters}.items()
        if values
    }
    return combined


def _normalize_sequence(values: Sequence[object] | None) -> list[object] | None:
    if values is None:
        return None
    items = list(values)
    return items or None


class _Paging:
    __slots__ = ("skip", "take")

    def __init__(self, skip: int, take: int) -> None:
        self.skip = skip
        self.take = take


def _resolve_paging(
    skip: int | None,
    take: int | None,
    settings: PublicServerSettings,
) -> _Paging:
    resolved_skip = settings.default_skip if skip is None else skip
    resolved_take = settings.default_take if take is None else take
    return _Paging(resolved_skip, resolved_take)


def _resolve_sort(
    sort: Sequence[tuple[ServiceField, SortDirection]] | None,
    settings: PublicServerSettings,
) -> Sequence[Sequence[str]] | None:
    if sort:
        return [[field, direction] for field, direction in sort]

    default_pairs = _parse_default_sort(settings.default_sort)
    if not default_pairs:
        return None
    return [[field, direction] for field, direction in default_pairs]


def _parse_default_sort(value: str | None) -> list[tuple[str, str]]:
    if not value:
        return []
    tokens = [token for token in value.split(",") if token]
    return list(zip(tokens[::2], tokens[1::2]))


__all__ = ["register_services_tools"]
