"""Static MCP tool definitions for Miggo's public API surface."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BeforeValidator, Field, WithJsonSchema

from ..client import MiggoPublicClient
from ..config import PublicServerSettings
from ..constants import (
    API_MAX_PAGE_SIZE,
    DEPENDENCY_DEFAULT_SORT,
    ENDPOINT_DEFAULT_SORT,
    FINDING_DEFAULT_SORT,
    MAX_PAGE_SIZE,
    THIRD_PARTY_DEFAULT_SORT,
    VULNERABILITY_DEFAULT_SORT,
    DependencyField,
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

ToolCallable = Callable[..., Awaitable[dict[str, object]]]

_READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


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
# TODO: Claude with cursor *sometimes* has problem with these tool calls,
# passing in a string which fails conversion. It's oddly difficult to debug what
# calls are happening in practice
Skip = Annotated[
    int | None,
    BeforeValidator(_parse_skip),
    WithJsonSchema({"type": "integer", "nullable": True}),
]
Take = Annotated[
    int | None,
    BeforeValidator(_parse_take),
    WithJsonSchema({"type": "integer", "nullable": True}),
]


def register_all_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register the complete set of Miggo public MCP tools."""
    tools: dict[str, Callable[..., Awaitable[dict[str, object]]]] = {}
    tools.update(register_services_tools(server, settings, client))
    tools.update(register_endpoints_tools(server, settings, client))
    tools.update(register_third_parties_tools(server, settings, client))
    tools.update(register_findings_tools(server, settings, client))
    tools.update(register_vulnerabilities_tools(server, settings, client))
    tools.update(register_dependencies_tools(server, settings, client))
    tools.update(register_project_tools(server, settings, client))
    return tools


def register_services_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for Miggo services endpoints."""
    default_sort = _parse_default_sort(settings.default_sort)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def services_search(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search for services in your Miggo environment. Use to get an
        overview of what's running and get a feel for what's available.

        Data fields:
        - id: service ID
        - name: service name (nullable)
        - isInternetFacing: internet-exposed flag (nullable)
        - isAuthenticated: requires auth flag (nullable)
        - type: resource type ("service")
        - isThirdPartyCommunication: connects to third parties
        - dataSensitivity: sensitivity tags (PII | PCI | PHI | SECRET | TOKEN)
        - createdAt: created timestamp
        - updatedAt: updated timestamp
        - technology: primary technology/language (nullable)
        - lastAccessed: last access timestamp (nullable)
        - sources: source systems
        - domains: associated domains
        - risk: risk score or label (string | number | null)
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
        )

        sort_params = _resolve_sort(sort, default_sort)
        payload = await _fetch_collection_pages(
            client,
            "/v1/services/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def services_get(
        service_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single service by id.

        Returns:
        - data: Service object (see fields listed in services_list)
        - meta: optional metadata if present in API response
        - status: optional HTTP status code from Miggo
        """
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

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def services_count(
        *,
        ids: Sequence[str] | None = None,
        names: Sequence[str] | None = None,
        is_internet_facing: bool | None = None,
        is_third_party_communication: bool | None = None,
        is_authenticated: bool | None = None,
        technologies: Sequence[str] | None = None,
        risks: Sequence[str] | None = None,
    ) -> dict[str, object]:
        """Count services matching filters.

        Purpose: Quickly assess result size or drive pagination UI without fetching records.

        Returns:
        - data: integer total count
        """
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
        )

        params = compose_params(filters=filters)

        payload = await client.get("/v1/services/count", params=params)

        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
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
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ServiceField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Get possible field values for service objects.

        Returns:
        - data: object mapping fieldName -> list of string values
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            name=names,
            isInternetFacing=is_internet_facing,
            isThirdPartyCommunication=is_third_party_communication,
            isAuthenticated=is_authenticated,
            technology=technologies,
            risk=risks,
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

    return {
        "services_search": services_search,
        "services_get": services_get,
        "services_count": services_count,
        "services_facets": services_facets,
    }


def register_endpoints_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for Miggo endpoint resources."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def endpoints_search(
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
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[EndpointField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search for endpoints in your Miggo environment. Use when more
        in-depth understanding of the environment is needed, or when looking
        for specific endpoints or how services are connected.

        Data fields:
        - id: endpoint ID
        - type: resource type ("endpoint")
        - apiType: API style (nullable)
        - action: HTTP method/action (nullable)
        - route: path/route pattern (nullable)
        - risk: risk score (number | null)
        - serviceId: parent service ID (nullable)
        - dataSensitivity: sensitivity tags (PII | PCI | PHI | SECRET | TOKEN)
        - domains: associated domains
        - isInternetFacing: internet-exposed flag
        - isAuthenticated: requires auth flag
        - isThirdPartyCommunication: connects to third parties
        """
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
        )

        sort_params = _resolve_sort(sort, ENDPOINT_DEFAULT_SORT)
        payload = await _fetch_collection_pages(
            client,
            "/v1/endpoints/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def endpoints_get(
        endpoint_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single endpoint by id.

        Returns:
        - data: Endpoint object (see fields listed in endpoints_list)
        """
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

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
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
    ) -> dict[str, object]:
        """Count the number of endpoints matching the given filters.

        Returns:
        - data: integer total count
        """
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
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/endpoints/count", params=params)
        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
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
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[EndpointField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Get possible field values for endpoint objects.

        Returns:
        - data: object mapping fieldName -> list of string values
        """
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

    return {
        "endpoints_search": endpoints_search,
        "endpoints_get": endpoints_get,
        "endpoints_count": endpoints_count,
        "endpoints_facets": endpoints_facets,
    }


def register_third_parties_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for third-party relationship endpoints."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def third_parties_search(
        *,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ThirdPartyField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search for third-parties in your Miggo environment. These are
        services external to the environment, like SaaS vendors. Use when
        there's a need to assess third-party risk, data exposure, or compliance

        Data fields:
        - id: third-party ID
        - type: resource type ("third-party")
        - domain: third-party domain
        - service: which service calls this third party
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
        )

        sort_params = _resolve_sort(sort, THIRD_PARTY_DEFAULT_SORT)
        payload = await _fetch_collection_pages(
            client,
            "/v1/third-parties/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def third_parties_get(
        third_party_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single third-party by id.

        Returns:
        - data: ThirdParty object (see fields listed in third_parties_list)
        """
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

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def third_parties_count(
        *,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
    ) -> dict[str, object]:
        """Count the number of third-parties matching the given filters.

        Returns:
        - data: integer total count
        """
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/third-parties/count", params=params)
        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def third_parties_facets(
        *,
        fields: Sequence[ThirdPartyField] | None = None,
        ids: Sequence[str] | None = None,
        domains: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[ThirdPartyField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Get possible field values for third-party objects.

        Returns:
        - data: object mapping fieldName -> list of string values
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            domain=domains,
            service=service_names,
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

    return {
        "third_parties_search": third_parties_search,
        "third_parties_get": third_parties_get,
        "third_parties_count": third_parties_count,
        "third_parties_facets": third_parties_facets,
    }


def register_findings_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for findings endpoints."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def findings_search(
        *,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[FindingField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search security findings.

        Purpose: Search posture/drift/incidents with filters/sort/paging.

        Data fields:
        - id: finding ID
        - type: category (THREAT_DETECTION | POSTURE | DRIFT | INCIDENT)
        - findingSubType: subtype label (nullable)
        - severity: severity level
        - status: lifecycle status
        - name: finding title
        - description: finding details
        - ruleId: rule identifier
        - entities: related entities (endpoint/external-service/service/third-party/data-source/dns-record/cloud-resource/domain/vulnerability/cve_name)
        - detectedAt: detection timestamp
        - remediation: remediation guidance (nullable)
        - createdAt: created timestamp
        - updatedAt: updated timestamp
        - evidence: evidence items (configuration/custom/span/trace/stack-trace/markdown/process_tree)
        - values: additional key-value data
        - attackStep: attack step (access/penetration/exploitation/impact/null)
        - mitigation: mitigation guidance (nullable)
        - tenantId: tenant identifier
        - projectId: project identifier
        - ticketId: external ticket id (nullable)
        - sensitiveData: sensitivity tags (PII | PCI | PHI | SECRET | TOKEN) (nullable)
        - ruleName: rule name (nullable)
        - policyName: policy name (nullable)
        - ticket: linked ticket object (nullable)
        - isInternetFacing: internet-exposed flag (nullable)
        - isWafProtected: WAF protection flag (nullable)
        - is3rdPartyAccess: third-party access flag (nullable)
        - isEncrypted: encryption flag (nullable)
        - isAuthorized: authorization enforced flag (nullable)
        - isAuthenticated: authentication enforced flag (nullable)
        - summary: short summary (nullable)
        - story: attack story steps (nullable)
        - account: cloud account (nullable)
        - region: cloud region (nullable)
        - cluster: cluster name (nullable)
        - namespace: namespace (nullable)
        - deployment: deployment name (nullable)
        - pod: pod name (nullable)
        - container: container name (nullable)
        - entityType: primary entity type (nullable)
        - indicator: indicator list (e.g., isInternetFacing) (nullable)
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
        )

        sort_params = _resolve_sort(sort, FINDING_DEFAULT_SORT)
        payload = await _fetch_collection_pages(
            client,
            "/v1/findings/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def findings_get(
        finding_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single finding by id.

        Purpose: Retrieve a Finding record for details or joins.

        Returns:
        - data: Finding object (see fields listed in findings_list)
        - meta: optional metadata if present in API response
        - status: optional HTTP status code from Miggo
        """
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

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def findings_count(
        *,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
    ) -> dict[str, object]:
        """Count findings matching filters.

        Purpose: Determine result size or drive pagination without fetching records.

        Returns:
        - data: integer total count
        """
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/findings/count", params=params)
        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def findings_facets(
        *,
        fields: Sequence[FindingField] | None = None,
        ids: Sequence[str] | None = None,
        types: Sequence[FindingType] | None = None,
        severities: Sequence[FindingSeverity] | None = None,
        statuses: Sequence[FindingStatus] | None = None,
        descriptions: Sequence[str] | None = None,
        rule_ids: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[FindingField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Retrieve facets for findings.

        Purpose: Get possible field values after filters to power filters/auto-complete.

        Returns:
        - data: object mapping fieldName -> list of string values
        - meta: object with query info (sort/take/skip) when provided
        - status: optional HTTP status code from Miggo
        """
        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            id=ids,
            type=types,
            severity=severities,
            status=statuses,
            description=descriptions,
            ruleId=rule_ids,
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

    return {
        "findings_search": findings_search,
        "findings_get": findings_get,
        "findings_count": findings_count,
        "findings_facets": findings_facets,
    }


def register_vulnerabilities_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for vulnerability endpoints."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def vulnerabilities_search(
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
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[VulnerabilityField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search known vulnerabilities.

        Purpose: Search vulnerabilities across services/images/packages with filters/sort/paging.

        Data fields:
        - id: vulnerability record ID
        - cvss: CVSS score (nullable)
        - cwe: CWE identifier (nullable)
        - dependencyStatus: execution status (STATIC | LOADED | EXECUTED | FUNCTION EXECUTED | null)
        - imageName: image name (nullable)
        - severity: severity level
        - serviceId: related service ID (nullable)
        - status: lifecycle status (nullable)
        - serviceName: related service name (nullable)
        - serviceSensitivitiesTags: service sensitivity tags (nullable)
        - lastSeen: last seen timestamp
        - createdAt: created timestamp
        - updatedAt: updated timestamp
        - isInternetFacing: internet-exposed flag
        - cluster: cluster name (nullable)
        - namespace: namespace (nullable)
        - type: resource type ("vulnerability")
        - vulnId: vulnerability identifier (nullable)
        - package: affected package name
        - hasPublicFix: public fix available flag
        - fixedVersions: fixed version list (nullable)
        """
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
            isInternetFacing=is_internet_facing,
            fixedVersions=fixed_versions,
            vulnId=vulnerability_ids,
            package=packages,
            hasPublicFix=has_public_fix,
        )

        sort_params = _resolve_sort(sort, VULNERABILITY_DEFAULT_SORT)
        payload = await _fetch_collection_pages(
            client,
            "/v1/vulnerabilities/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def vulnerabilities_get(
        vulnerability_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single vulnerability by id.

        Purpose: Retrieve a Vulnerability record for details or joins.

        Returns:
        - data: Vulnerability object (see fields listed in vulnerabilities_list)
        - meta: optional metadata if present in API response
        - status: optional HTTP status code from Miggo
        """
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

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
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
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
    ) -> dict[str, object]:
        """Count vulnerabilities matching filters.

        Purpose: Determine result size or drive pagination without fetching records.

        Returns:
        - data: integer total count
        """
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
            isInternetFacing=is_internet_facing,
            fixedVersions=fixed_versions,
            vulnId=vulnerability_ids,
            package=packages,
            hasPublicFix=has_public_fix,
        )

        params = compose_params(filters=filters)
        payload = await client.get("/v1/vulnerabilities/count", params=params)
        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
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
        is_internet_facing: bool | None = None,
        fixed_versions: Sequence[str] | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        packages: Sequence[str] | None = None,
        has_public_fix: bool | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[VulnerabilityField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Retrieve facets for vulnerabilities.

        Purpose: Get possible field values after filters to power filters/auto-complete.

        Returns:
        - data: object mapping fieldName -> list of string values
        - meta: object with query info (sort/take/skip) when provided
        - status: optional HTTP status code from Miggo
        """
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

    return {
        "vulnerabilities_search": vulnerabilities_search,
        "vulnerabilities_get": vulnerabilities_get,
        "vulnerabilities_count": vulnerabilities_count,
        "vulnerabilities_facets": vulnerabilities_facets,
    }


def register_dependencies_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools for dependency endpoints."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def dependencies_search(
        *,
        names: Sequence[str] | None = None,
        versions: Sequence[str] | None = None,
        name_and_versions: Sequence[str] | None = None,
        image_names: Sequence[str] | None = None,
        latest_versions: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        statuses: Sequence[str] | None = None,
        languages: Sequence[str] | None = None,
        last_seen: Sequence[float] | None = None,
        is_service_internet_facing: bool | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[DependencyField, SortDirection]] | None = None,
    ) -> dict[str, object]:
        """Search software dependencies across services and images.

        Data fields:
        - id: dependency ID
        - type: resource type ("dependency")
        - name: dependency package name
        - version: currently detected version
        - nameAndVersion: combined identifier (e.g., package@version)
        - imageName: associated container image (nullable)
        - latestVersion: Miggo's latest known version
        - serviceName: service using the dependency
        - status: lifecycle status string (e.g., up_to_date)
        - language: ecosystem/language identifier
        - lastSeen: last observed timestamp (epoch milliseconds)
        - firstSeen: first observed timestamp (epoch milliseconds)
        - createdAt / updatedAt: record timestamps
        - isServiceInternetFacing: whether the owning service is internet-exposed
        - vulnerabilities: related vulnerability summaries
        """

        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            name=names,
            version=versions,
            nameAndVersion=name_and_versions,
            imageName=image_names,
            latestVersion=latest_versions,
            serviceName=service_names,
            status=statuses,
            language=languages,
            lastSeen=last_seen,
            isServiceInternetFacing=is_service_internet_facing,
            vulnerabilities=vulnerability_ids,
        )

        sort_params = _resolve_sort(sort, DEPENDENCY_DEFAULT_SORT)
        payload = await _fetch_collection_pages(
            client,
            "/v1/dependencies/",
            filters=filters,
            skip=paging.skip,
            take=paging.take,
            sort=sort_params,
        )
        return collection_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def dependencies_get(
        dependency_id: Annotated[str, Field(min_length=1)],
    ) -> dict[str, object]:
        """Fetch a single dependency by id."""

        params = compose_params(
            filters={"id": [dependency_id]},
            take=1,
            sort=_resolve_sort(None, DEPENDENCY_DEFAULT_SORT),
        )

        payload = await client.get("/v1/dependencies/", params=params)

        dependencies = payload.get("data") or []
        if not dependencies:
            raise ValueError(f"No dependency found for id {dependency_id!r}")

        response = {"data": dependencies[0]}
        meta = payload.get("meta")
        if isinstance(meta, Mapping) and meta:
            response["meta"] = meta
        return response

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def dependencies_count(
        *,
        names: Sequence[str] | None = None,
        versions: Sequence[str] | None = None,
        name_and_versions: Sequence[str] | None = None,
        image_names: Sequence[str] | None = None,
        latest_versions: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        statuses: Sequence[str] | None = None,
        languages: Sequence[str] | None = None,
        last_seen: Sequence[float] | None = None,
        is_service_internet_facing: bool | None = None,
        vulnerability_ids: Sequence[str] | None = None,
    ) -> dict[str, object]:
        """Count dependencies matching filters.

        Returns:
        - data: integer total count
        """

        filters = _build_where_filters(
            name=names,
            version=versions,
            nameAndVersion=name_and_versions,
            imageName=image_names,
            latestVersion=latest_versions,
            serviceName=service_names,
            status=statuses,
            language=languages,
            lastSeen=last_seen,
            isServiceInternetFacing=is_service_internet_facing,
            vulnerabilities=vulnerability_ids,
        )

        params = compose_params(filters=filters)

        payload = await client.get("/v1/dependencies/count", params=params)
        return scalar_response(payload)

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def dependencies_facets(
        *,
        fields: Sequence[DependencyField] | None = None,
        names: Sequence[str] | None = None,
        versions: Sequence[str] | None = None,
        name_and_versions: Sequence[str] | None = None,
        image_names: Sequence[str] | None = None,
        latest_versions: Sequence[str] | None = None,
        service_names: Sequence[str] | None = None,
        statuses: Sequence[str] | None = None,
        languages: Sequence[str] | None = None,
        last_seen: Sequence[float] | None = None,
        is_service_internet_facing: bool | None = None,
        vulnerability_ids: Sequence[str] | None = None,
        skip: Skip = None,
        take: Take = None,
        sort: Sequence[tuple[DependencyField, SortDirection]] | None = None,
        search: Annotated[str | None, Field(min_length=1)] = None,
    ) -> dict[str, object]:
        """Get possible field values for dependency objects."""

        paging = _resolve_paging(skip, take, settings)
        filters = _build_where_filters(
            name=names,
            version=versions,
            nameAndVersion=name_and_versions,
            imageName=image_names,
            latestVersion=latest_versions,
            serviceName=service_names,
            status=statuses,
            language=languages,
            lastSeen=last_seen,
            isServiceInternetFacing=is_service_internet_facing,
            vulnerabilities=vulnerability_ids,
        )

        params = compose_params(
            filters=filters,
            fields=fields,
            skip=paging.skip,
            take=paging.take,
            sort=_resolve_sort(sort, DEPENDENCY_DEFAULT_SORT),
            search=search,
        )

        payload = await client.get("/v1/dependencies/facets", params=params)
        return collection_response(payload)

    return {
        "dependencies_search": dependencies_search,
        "dependencies_get": dependencies_get,
        "dependencies_count": dependencies_count,
        "dependencies_facets": dependencies_facets,
    }


def register_project_tools(
    server: FastMCP,
    settings: PublicServerSettings,
    client: MiggoPublicClient,
) -> dict[str, Callable[..., Awaitable[dict[str, object]]]]:
    """Register tools that expose Miggo project metadata."""

    @server.tool(annotations=_READ_ONLY_ANNOTATIONS)
    async def project_get() -> dict[str, object]:
        """Return metadata for the authenticated project.

        Purpose: Identify the current project context for scoping and display.

        Returns:
        - data: object with fields tenantId, projectId, projectName
        - status: optional HTTP status code from Miggo
        """
        payload = await client.get("/v1/project/")
        return collection_response(payload)

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
    if isinstance(value, str | bytes):
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


async def _fetch_collection_pages(
    client: MiggoPublicClient,
    path: str,
    *,
    filters: Mapping[str, object] | None = None,
    skip: int,
    take: int,
    sort: Sequence[Sequence[str]] | None = None,
    search: str | None = None,
    fields: Sequence[str] | None = None,
    extra: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Fetch a Miggo collection endpoint honoring ``take`` via client-side paging."""
    if take <= 0:
        return {
            "data": [],
            "meta": {
                "query": {
                    "skip": skip,
                    "take": take,
                    "pagesFetched": 0,
                    "fetched": 0,
                }
            },
        }

    remaining = take
    next_skip = skip
    collected: list[Any] = []
    aggregated_meta: dict[str, Any] | None = None
    status_value: Any = None
    pages = 0

    while remaining > 0:
        chunk_take = min(API_MAX_PAGE_SIZE, remaining)
        params = compose_params(
            filters=filters,
            skip=next_skip,
            take=chunk_take,
            sort=sort,
            search=search,
            fields=fields,
            extra=extra,
        )
        payload = await client.get(path, params=params)
        data = payload.get("data")
        if not isinstance(data, list):
            return payload

        collected.extend(data)

        page_status = payload.get("status")
        if page_status is not None:
            status_value = page_status

        meta = payload.get("meta")
        if aggregated_meta is None:
            aggregated_meta = dict(meta) if isinstance(meta, Mapping) else {}
        elif isinstance(meta, Mapping):
            for key, value in meta.items():
                aggregated_meta.setdefault(key, value)

        pages += 1
        count = len(data)
        remaining -= count
        if remaining <= 0:
            break
        if count < chunk_take:
            break
        next_skip += count

    meta_out: dict[str, Any] = {}
    if aggregated_meta:
        meta_out = dict(aggregated_meta)
    query_meta = meta_out.get("query")
    if isinstance(query_meta, Mapping):
        query_meta = dict(query_meta)
    else:
        query_meta = {}
    query_meta.update(
        {
            "skip": skip,
            "take": take,
            "pagesFetched": pages,
            "fetched": len(collected),
        }
    )
    meta_out["query"] = query_meta

    result: dict[str, Any] = {"data": collected}
    if meta_out:
        result["meta"] = meta_out
    if status_value is not None:
        result["status"] = status_value
    return result


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
    return list(zip(tokens[::2], tokens[1::2], strict=False))


__all__ = [
    "register_all_tools",
    "register_endpoints_tools",
    "register_findings_tools",
    "register_dependencies_tools",
    "register_project_tools",
    "register_services_tools",
    "register_third_parties_tools",
    "register_vulnerabilities_tools",
]
