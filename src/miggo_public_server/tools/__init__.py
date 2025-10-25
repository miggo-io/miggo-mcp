"""Static MCP tool definitions for Miggo's public API surface."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Mapping, MutableMapping, Sequence, TypeVar

from mcp.server.fastmcp import FastMCP
from pydantic import BeforeValidator, Field, validate_call

from ..client import MiggoPublicClient
from ..config import PublicServerSettings
from ..constants import (
    ENDPOINT_DEFAULT_SORT,
    FINDING_DEFAULT_SORT,
    MAX_PAGE_SIZE,
    THIRD_PARTY_DEFAULT_SORT,
    VULNERABILITY_DEFAULT_SORT,
    EndpointField,
    FindingField,
    FindingSeverity,
    FindingStatus,
    FindingType,
    ServiceField,
    SortDirection,
    ThirdPartyField,
    VulnerabilityDependencyStatus,
    VulnerabilityField,
    VulnerabilitySeverity,
    VulnerabilityStatus,
)
from ..query import compose_params
from ..response import collection_response, scalar_response

ToolCallable = Callable[..., Awaitable[MutableMapping[str, object]]]
_ToolCallableT = TypeVar("_ToolCallableT", bound=ToolCallable)


def _parse_skip(value: int | float | None) -> int | None:
    """Parse and validate skip parameter, converting from float if needed."""
    if value is None:
        return None
    # Pydantic may coerce int to float; convert back
    int_value = int(value)
    if value != int_value:
        raise ValueError(f"skip must be an integer, got {value}")
    if int_value < 0:
        raise ValueError(f"skip must be non-negative, got {int_value}")
    return int_value


def _parse_take(value: int | float | None) -> int | None:
    """Parse and validate take parameter, converting from float if needed."""
    if value is None:
        return None
    # Pydantic may coerce int to float; convert back
    int_value = int(value)
    if value != int_value:
        raise ValueError(f"take must be an integer, got {value}")
    if int_value < 0:
        raise ValueError(f"take must be non-negative, got {int_value}")
    if int_value > MAX_PAGE_SIZE:
        raise ValueError(f"take must be <= {MAX_PAGE_SIZE}, got {int_value}")
    return int_value


# Type aliases for paging parameters with validation
Skip = Annotated[int | None, BeforeValidator(_parse_skip)]
Take = Annotated[int | None, BeforeValidator(_parse_take)]


def register_all_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register the complete set of Miggo public MCP tools."""
    tools: dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]] = {}
    tools.update(register_services_tools(server, settings, client))
    tools.update(register_endpoints_tools(server, settings, client))
    tools.update(register_third_parties_tools(server, settings, client))
    tools.update(register_findings_tools(server, settings, client))
    tools.update(register_vulnerabilities_tools(server, settings, client))
    tools.update(register_project_tools(server, settings, client))
    return tools


def register_services_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools for Miggo services endpoints."""
    default_sort = _parse_default_sort(settings.default_sort)

    async def services_list(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        last_accessed: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List Miggo services with optional filtering, sorting, and pagination."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
            createdAt=created_at,
            updatedAt=updated_at,
            lastAccessed=last_accessed,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, default_sort),
        )

        payload = await client.get("/v1/services/", params=params)
        return collection_response(payload)

    services_list = _register_tool(server, services_list)

    async def services_get(
        service_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a single Miggo service by identifier."""
        params = compose_params(
            filters={"id": [service_id]},
            take=1,
            sort=_resolve_sort(None, default_sort),
        )

        payload = await client.get("/v1/services/", params=params)

        services = payload.get("data") or []
        if not services:
            raise ValueError(f"No service found for id {service_id!r}")

        response = {"data": services[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    services_get = _register_tool(server, services_get)

    async def services_count(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        last_accessed: Sequence[int] | None = None,
    ) -> MutableMapping[str, object]:
        """Return a count of services matching the provided filters."""
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
            createdAt=created_at,
            updatedAt=updated_at,
            lastAccessed=last_accessed,
        )

        params = compose_params(filters=filters)

        payload = await client.get("/v1/services/count", params=params)

        return scalar_response(payload)

    services_count = _register_tool(server, services_count)

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
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        last_accessed: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets (distinct field values) for the services dataset."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
            createdAt=created_at,
            updatedAt=updated_at,
            lastAccessed=last_accessed,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, default_sort),
            search=search,
        )

        payload = await client.get("/v1/services/facets", params=params)
        return collection_response(payload)

    services_facets = _register_tool(server, services_facets)

    return {
        "services_list": services_list,
        "services_get": services_get,
        "services_count": services_count,
        "services_facets": services_facets,
    }


def register_endpoints_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools for Miggo endpoint resources."""

    async def endpoints_list(
        *,
        ids: Sequence[str] | None = None,
        actions: Sequence[str] | None = None,
        routes: Sequence[str] | None = None,
        service_ids: Sequence[str] | None = None,
        data_sensitivities: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_authenticated: bool | None = None,
        is_third_party_communication: bool | None = None,
        risk_scores: Sequence[float] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[EndpointField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List Miggo endpoints with optional filtering and pagination."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            action=actions,
            route=routes,
            serviceId=service_ids,
            dataSensitivity=data_sensitivities,
            isInternetFacing=is_internet_facing,
            isAuthenticated=is_authenticated,
            isThirdPartyCommunication=is_third_party_communication,
            risk=risk_scores,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, ENDPOINT_DEFAULT_SORT),
        )

        payload = await client.get("/v1/endpoints/", params=params)
        return collection_response(payload)

    endpoints_list = _register_tool(server, endpoints_list)

    async def endpoints_get(
        endpoint_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a single endpoint by identifier."""
        params = compose_params(
            filters={"id": [endpoint_id]},
            take=1,
            sort=_resolve_sort(None, ENDPOINT_DEFAULT_SORT),
        )
        payload = await client.get("/v1/endpoints/", params=params)

        endpoints = payload.get("data") or []
        if not endpoints:
            raise ValueError(f"No endpoint found for id {endpoint_id!r}")

        response = {"data": endpoints[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    endpoints_get = _register_tool(server, endpoints_get)

    async def endpoints_count(
        *,
        ids: Sequence[str] | None = None,
        actions: Sequence[str] | None = None,
        routes: Sequence[str] | None = None,
        service_ids: Sequence[str] | None = None,
        data_sensitivities: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_authenticated: bool | None = None,
        is_third_party_communication: bool | None = None,
        risk_scores: Sequence[float] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
    ) -> MutableMapping[str, object]:
        """Count endpoints matching the provided filters."""
        filters = _build_where_filters(
            id=ids,
            action=actions,
            route=routes,
            serviceId=service_ids,
            dataSensitivity=data_sensitivities,
            isInternetFacing=is_internet_facing,
            isAuthenticated=is_authenticated,
            isThirdPartyCommunication=is_third_party_communication,
            risk=risk_scores,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/endpoints/count", params=params)
        return scalar_response(payload)

    endpoints_count = _register_tool(server, endpoints_count)

    async def endpoints_facets(
        *,
        fields: Sequence[EndpointField] | None = None,
        ids: Sequence[str] | None = None,
        actions: Sequence[str] | None = None,
        routes: Sequence[str] | None = None,
        service_ids: Sequence[str] | None = None,
        data_sensitivities: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_authenticated: bool | None = None,
        is_third_party_communication: bool | None = None,
        risk_scores: Sequence[float] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[EndpointField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets for endpoint resources."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            action=actions,
            route=routes,
            serviceId=service_ids,
            dataSensitivity=data_sensitivities,
            isInternetFacing=is_internet_facing,
            isAuthenticated=is_authenticated,
            isThirdPartyCommunication=is_third_party_communication,
            risk=risk_scores,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, ENDPOINT_DEFAULT_SORT),
            search=search,
        )

        payload = await client.get("/v1/endpoints/facets", params=params)
        return collection_response(payload)

    endpoints_facets = _register_tool(server, endpoints_facets)

    return {
        "endpoints_list": endpoints_list,
        "endpoints_get": endpoints_get,
        "endpoints_count": endpoints_count,
        "endpoints_facets": endpoints_facets,
    }


def register_third_parties_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools for third-party relationship endpoints."""

    async def third_parties_list(
        *,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ThirdPartyField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List third-party integrations."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, THIRD_PARTY_DEFAULT_SORT),
        )

        payload = await client.get("/v1/third-parties/", params=params)
        return collection_response(payload)

    third_parties_list = _register_tool(server, third_parties_list)

    async def third_parties_get(
        third_party_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a specific third-party integration by identifier."""
        params = compose_params(
            filters={"id": [third_party_id]},
            take=1,
            sort=_resolve_sort(None, THIRD_PARTY_DEFAULT_SORT),
        )
        payload = await client.get("/v1/third-parties/", params=params)

        third_parties = payload.get("data") or []
        if not third_parties:
            raise ValueError(f"No third-party found for id {third_party_id!r}")

        response = {"data": third_parties[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    third_parties_get = _register_tool(server, third_parties_get)

    async def third_parties_count(
        *,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
    ) -> MutableMapping[str, object]:
        """Count third-party integrations matching the provided filters."""
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/third-parties/count", params=params)
        return scalar_response(payload)

    third_parties_count = _register_tool(server, third_parties_count)

    async def third_parties_facets(
        *,
        fields: Sequence[ThirdPartyField] | None = None,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        first_seen: Sequence[int] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ThirdPartyField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets for third-party integrations."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
            firstSeen=first_seen,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, THIRD_PARTY_DEFAULT_SORT),
            search=search,
        )
        payload = await client.get("/v1/third-parties/facets", params=params)
        return collection_response(payload)

    third_parties_facets = _register_tool(server, third_parties_facets)

    return {
        "third_parties_list": third_parties_list,
        "third_parties_get": third_parties_get,
        "third_parties_count": third_parties_count,
        "third_parties_facets": third_parties_facets,
    }


def register_findings_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools for findings endpoints."""

    async def findings_list(
        *,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[FindingField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List security findings."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, FINDING_DEFAULT_SORT),
        )

        payload = await client.get("/v1/findings/", params=params)
        return collection_response(payload)

    findings_list = _register_tool(server, findings_list)

    async def findings_get(
        finding_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a single finding by identifier."""
        params = compose_params(
            filters={"id": [finding_id]},
            take=1,
            sort=_resolve_sort(None, FINDING_DEFAULT_SORT),
        )
        payload = await client.get("/v1/findings/", params=params)

        findings = payload.get("data") or []
        if not findings:
            raise ValueError(f"No finding found for id {finding_id!r}")

        response = {"data": findings[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    findings_get = _register_tool(server, findings_get)

    async def findings_count(
        *,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
    ) -> MutableMapping[str, object]:
        """Count findings matching the provided filters."""
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/findings/count", params=params)
        return scalar_response(payload)

    findings_count = _register_tool(server, findings_count)

    async def findings_facets(
        *,
        fields: Sequence[FindingField] | None = None,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[FindingField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets for findings."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
            createdAt=created_at,
            updatedAt=updated_at,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, FINDING_DEFAULT_SORT),
            search=search,
        )
        payload = await client.get("/v1/findings/facets", params=params)
        return collection_response(payload)

    findings_facets = _register_tool(server, findings_facets)

    return {
        "findings_list": findings_list,
        "findings_get": findings_get,
        "findings_count": findings_count,
        "findings_facets": findings_facets,
    }


def register_vulnerabilities_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools for vulnerability endpoints."""

    async def vulnerabilities_list(
        *,
        ids: Sequence[str] | None = None,
        cvss_scores: Sequence[str] | None = None,
        dependency_statuses: Sequence[VulnerabilityDependencyStatus] | None = None,
        image_names: Sequence[str] | None = None,
        severities: Sequence[VulnerabilitySeverity] | None = None,
        service_ids: Sequence[str] | None = None,
        statuses: Sequence[VulnerabilityStatus] | None = None,
        service_names: Sequence[str] | None = None,
        service_sensitivity_tags: Sequence[str] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[VulnerabilityField, SortDirection]] | None = None,
    ) -> MutableMapping[str, object]:
        """List known vulnerabilities."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            cvss=cvss_scores,
            dependencyStatus=dependency_statuses,
            imageName=image_names,
            severity=severities,
            serviceId=service_ids,
            status=statuses,
            serviceName=service_names,
            serviceSensitivitiesTags=service_sensitivity_tags,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
            isInternetFacing=is_internet_facing,
            fixedVersions=fixed_versions,
            vulnId=vulnerability_ids,
            package=packages,
            hasPublicFix=has_public_fix,
        )

        params = compose_params(
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, VULNERABILITY_DEFAULT_SORT),
        )
        payload = await client.get("/v1/vulnerabilities/", params=params)
        return collection_response(payload)

    vulnerabilities_list = _register_tool(server, vulnerabilities_list)

    async def vulnerabilities_get(
        vulnerability_id: Annotated[str, Field(min_length=1)],
    ) -> MutableMapping[str, object]:
        """Fetch a single vulnerability by identifier."""
        params = compose_params(
            filters={"id": [vulnerability_id]},
            take=1,
            sort=_resolve_sort(None, VULNERABILITY_DEFAULT_SORT),
        )
        payload = await client.get("/v1/vulnerabilities/", params=params)

        vulnerabilities = payload.get("data") or []
        if not vulnerabilities:
            raise ValueError(f"No vulnerability found for id {vulnerability_id!r}")

        response = {"data": vulnerabilities[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    vulnerabilities_get = _register_tool(server, vulnerabilities_get)

    async def vulnerabilities_count(
        *,
        ids: Sequence[str] | None = None,
        cvss_scores: Sequence[str] | None = None,
        dependency_statuses: Sequence[VulnerabilityDependencyStatus] | None = None,
        image_names: Sequence[str] | None = None,
        severities: Sequence[VulnerabilitySeverity] | None = None,
        service_ids: Sequence[str] | None = None,
        statuses: Sequence[VulnerabilityStatus] | None = None,
        service_names: Sequence[str] | None = None,
        service_sensitivity_tags: Sequence[str] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
    ) -> MutableMapping[str, object]:
        """Count vulnerabilities matching the provided filters."""
        filters = _build_where_filters(
            id=ids,
            cvss=cvss_scores,
            dependencyStatus=dependency_statuses,
            imageName=image_names,
            severity=severities,
            serviceId=service_ids,
            status=statuses,
            serviceName=service_names,
            serviceSensitivitiesTags=service_sensitivity_tags,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
            isInternetFacing=is_internet_facing,
            fixedVersions=fixed_versions,
            vulnId=vulnerability_ids,
            package=packages,
            hasPublicFix=has_public_fix,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/vulnerabilities/count", params=params)
        return scalar_response(payload)

    vulnerabilities_count = _register_tool(server, vulnerabilities_count)

    async def vulnerabilities_facets(
        *,
        fields: Sequence[VulnerabilityField] | None = None,
        ids: Sequence[str] | None = None,
        cvss_scores: Sequence[str] | None = None,
        dependency_statuses: Sequence[VulnerabilityDependencyStatus] | None = None,
        image_names: Sequence[str] | None = None,
        severities: Sequence[VulnerabilitySeverity] | None = None,
        service_ids: Sequence[str] | None = None,
        statuses: Sequence[VulnerabilityStatus] | None = None,
        service_names: Sequence[str] | None = None,
        service_sensitivity_tags: Sequence[str] | None = None,
        last_seen: Sequence[int] | None = None,
        created_at: Sequence[int] | None = None,
        updated_at: Sequence[int] | None = None,
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[VulnerabilityField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> MutableMapping[str, object]:
        """Retrieve facets for vulnerabilities."""
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            cvss=cvss_scores,
            dependencyStatus=dependency_statuses,
            imageName=image_names,
            severity=severities,
            serviceId=service_ids,
            status=statuses,
            serviceName=service_names,
            serviceSensitivitiesTags=service_sensitivity_tags,
            lastSeen=last_seen,
            createdAt=created_at,
            updatedAt=updated_at,
            isInternetFacing=is_internet_facing,
            fixedVersions=fixed_versions,
            vulnId=vulnerability_ids,
            package=packages,
            hasPublicFix=has_public_fix,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, VULNERABILITY_DEFAULT_SORT),
            search=search,
        )
        payload = await client.get("/v1/vulnerabilities/facets", params=params)
        return collection_response(payload)

    vulnerabilities_facets = _register_tool(server, vulnerabilities_facets)

    return {
        "vulnerabilities_list": vulnerabilities_list,
        "vulnerabilities_get": vulnerabilities_get,
        "vulnerabilities_count": vulnerabilities_count,
        "vulnerabilities_facets": vulnerabilities_facets,
    }


def register_project_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[MutableMapping[str, object]]]]:
    """Register tools that expose Miggo project metadata."""

    async def project_get() -> MutableMapping[str, object]:
        """Return metadata for the authenticated project."""
        payload = await client.get("/v1/project/")
        return collection_response(payload)

    project_get = _register_tool(server, project_get)
    return {"project_get": project_get}


def _build_where_filters(**field_values: object) -> dict[str, list[object]]:
    """Translate keyword arguments into Miggo ``where`` filters."""
    filters: dict[str, list[object]] = {}
    for field, value in field_values.items():
        normalized = _normalize_sequence(value)
        if normalized:
            filters[field] = normalized
    return filters


def _normalize_sequence(value: object) -> list[object] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Sequence):
        items = [item for item in value if item is not None]
        return items or None
    return [value]


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
    sort: Sequence[tuple[str, SortDirection]] | None,
    default_pairs: Sequence[tuple[str, str]] | None,
) -> Sequence[Sequence[str]] | None:
    if sort:
        return [[field, direction] for field, direction in sort]
    if default_pairs:
        return [[field, direction] for field, direction in default_pairs]
    return None


def _parse_default_sort(value: str | None) -> list[tuple[str, str]]:
    if not value:
        return []
    tokens = [token for token in value.split(",") if token]
    return list(zip(tokens[::2], tokens[1::2]))


def _register_tool(server: FastMCP, func: _ToolCallableT) -> _ToolCallableT:
    """Apply pydantic validation with mode='json' for MCP compatibility."""
    from pydantic import ConfigDict
    
    validated = validate_call(func, config=ConfigDict(strict=False))
    _ensure_callable_globals(validated)
    registered = server.tool()(validated)
    return registered


def _ensure_callable_globals(func: ToolCallable) -> None:
    """Expose this module's typing symbols to decorated callables."""
    source_globals = globals()
    target_globals = func.__globals__
    for name in (
        "Sequence",
        "Annotated",
        "Field",
        "MutableMapping",
        "ServiceField",
        "EndpointField",
        "ThirdPartyField",
        "FindingField",
        "FindingType",
        "FindingSeverity",
        "FindingStatus",
        "VulnerabilityField",
        "VulnerabilityDependencyStatus",
        "VulnerabilitySeverity",
        "VulnerabilityStatus",
        "SortDirection",
        "MAX_PAGE_SIZE",
        "Skip",
        "Take",
    ):
        if name in source_globals and name not in target_globals:
            target_globals[name] = source_globals[name]


__all__ = [
    "register_all_tools",
    "register_endpoints_tools",
    "register_findings_tools",
    "register_project_tools",
    "register_services_tools",
    "register_third_parties_tools",
    "register_vulnerabilities_tools",
]
