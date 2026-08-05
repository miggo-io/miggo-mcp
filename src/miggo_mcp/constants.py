"""Shared constants and type aliases for the Miggo public FastMCP server."""

from __future__ import annotations

from typing import Literal

ServiceField = Literal[
    "id",
    "name",
    "isInternetFacing",
    "isThirdPartyCommunication",
    "isAuthenticated",
    "createdAt",
    "updatedAt",
    "technology",
    "lastAccessed",
    "risk",
]

SortDirection = Literal["asc", "desc"]

SERVICES_FIELDS = [
    "id",
    "name",
    "isInternetFacing",
    "isThirdPartyCommunication",
    "isAuthenticated",
    "createdAt",
    "updatedAt",
    "technology",
    "lastAccessed",
    "risk",
]

MAX_PAGE_SIZE = 1000
API_MAX_PAGE_SIZE = 50

DependencyField = Literal[
    "name",
    "version",
    "nameAndVersion",
    "imageName",
    "latestVersion",
    "serviceName",
    "status",
    "language",
    "lastSeen",
    "isServiceInternetFacing",
    "vulnerabilities",
]

DEPENDENCY_FIELDS = [
    "name",
    "version",
    "nameAndVersion",
    "imageName",
    "latestVersion",
    "serviceName",
    "status",
    "language",
    "lastSeen",
    "isServiceInternetFacing",
    "vulnerabilities",
]

DEPENDENCY_DEFAULT_SORT = [("vulnerabilities", "desc")]

EndpointField = Literal[
    "id",
    "action",
    "route",
    "firstSeen",
    "lastSeen",
    "updatedAt",
    "createdAt",
    "risk",
    "serviceId",
    "dataSensitivity",
    "isInternetFacing",
    "isAuthenticated",
    "isThirdPartyCommunication",
]

ENDPOINT_FIELDS = [
    "id",
    "action",
    "route",
    "firstSeen",
    "lastSeen",
    "updatedAt",
    "createdAt",
    "risk",
    "serviceId",
    "dataSensitivity",
    "isInternetFacing",
    "isAuthenticated",
    "isThirdPartyCommunication",
]

ENDPOINT_DEFAULT_SORT = [("risk", "desc")]

ThirdPartyField = Literal[
    "id",
    "domain",
    "firstSeen",
    "lastSeen",
    "createdAt",
    "updatedAt",
    "service",
]

THIRD_PARTY_FIELDS = [
    "id",
    "domain",
    "firstSeen",
    "lastSeen",
    "createdAt",
    "updatedAt",
    "service",
]

THIRD_PARTY_DEFAULT_SORT = [("lastSeen", "desc")]

FindingField = Literal[
    "id",
    "type",
    "severity",
    "status",
    "description",
    "ruleId",
    "createdAt",
    "updatedAt",
]

FindingType = Literal["THREAT_DETECTION", "POSTURE", "DRIFT", "INCIDENT"]

FindingSeverity = Literal["critical", "high", "medium", "low", "info"]

FindingStatus = Literal["OPEN", "IN_REVIEW", "RESOLVED", "DISMISSED"]

FINDING_FIELDS = [
    "id",
    "type",
    "severity",
    "status",
    "description",
    "ruleId",
    "createdAt",
    "updatedAt",
]

FINDING_DEFAULT_SORT = [("severity", "desc")]

VulnerabilityField = Literal[
    "id",
    "cvss",
    "dependencyStatus",
    "imageName",
    "severity",
    "serviceId",
    "status",
    "serviceName",
    "serviceSensitivitiesTags",
    "lastSeen",
    "createdAt",
    "updatedAt",
    "isInternetFacing",
    "fixedVersions",
    "vulnId",
    "package",
    "hasPublicFix",
]

VulnerabilityDependencyStatus = Literal[
    "STATIC",
    "LOADED",
    "EXECUTED",
    "FUNCTION EXECUTED",
]

VulnerabilitySeverity = Literal["critical", "high", "medium", "low", "info"]

VulnerabilityStatus = Literal["OPEN", "IN_REVIEW", "RESOLVED", "DISMISSED", "PATCHED"]

VULNERABILITY_FIELDS = [
    "id",
    "cvss",
    "dependencyStatus",
    "imageName",
    "severity",
    "serviceId",
    "status",
    "serviceName",
    "serviceSensitivitiesTags",
    "lastSeen",
    "createdAt",
    "updatedAt",
    "isInternetFacing",
    "fixedVersions",
    "vulnId",
    "package",
    "hasPublicFix",
]

VULNERABILITY_DEFAULT_SORT = [("cvss", "desc")]

DataSourceField = Literal[
    "id",
    "system",
    "dbName",
    "hostname",
    "dataSensitivity",
    "isSensitive",
    "isAiRelated",
    "firstSeen",
    "updatedAt",
]

# Sortable is a strict subset of filterable here, unlike the other domains.
DataSourceSortField = Literal[
    "system",
    "dbName",
    "hostname",
    "firstSeen",
    "updatedAt",
]

DATA_SOURCE_FIELDS = [
    "system",
    "dbName",
    "hostname",
    "firstSeen",
    "updatedAt",
]

DATA_SOURCE_DEFAULT_SORT = [("firstSeen", "desc")]

DataSourceTableField = Literal[
    "dataSourceId",
    "tableName",
    "dataSensitivity",
]

DataSourceTableSortField = Literal[
    "tableName",
    "firstSeen",
    "dataSensitivity",
]

DATA_SOURCE_TABLE_FIELDS = [
    "tableName",
    "firstSeen",
    "dataSensitivity",
]

DATA_SOURCE_TABLE_DEFAULT_SORT = [("dataSensitivity", "desc"), ("tableName", "asc")]

DomainField = Literal[
    "id",
    "name",
    "root",
    "serviceName",
    "edgeProtection",
    "isInternetFacing",
    "isAiRelated",
    "integrationsTypes",
    "createdAt",
    "updatedAt",
]

# `dnsRecords` is jsonb: returned, but neither sortable nor filterable.
DomainSortField = Literal[
    "name",
    "root",
    "serviceName",
    "edgeProtection",
    "isInternetFacing",
    "createdAt",
    "updatedAt",
]

DomainEdgeProtection = Literal["Protected", "Proxied", "Not Protected"]

DOMAIN_FIELDS = [
    "name",
    "root",
    "serviceName",
    "edgeProtection",
    "isInternetFacing",
    "createdAt",
    "updatedAt",
]

DOMAIN_DEFAULT_SORT = [("createdAt", "desc")]

CloudResourceField = Literal[
    "id",
    "name",
    "provider",
    "region",
    "resourceType",
    "cloudService",
    "isAiRelated",
    "lastSeen",
    "createdAt",
    "updatedAt",
]

CloudResourceSortField = Literal[
    "name",
    "provider",
    "region",
    "resourceType",
    "cloudService",
    "lastSeen",
    "createdAt",
    "updatedAt",
]

CLOUD_RESOURCE_FIELDS = [
    "name",
    "provider",
    "region",
    "resourceType",
    "cloudService",
    "lastSeen",
    "createdAt",
    "updatedAt",
]

CLOUD_RESOURCE_DEFAULT_SORT = [("lastSeen", "desc")]

# Service downstream sub-resources. All are filtered by a single required
# serviceId and share the get/count pagination shape, so one tool dispatches
# over them by ``kind`` rather than four near-identical tool families.
DownstreamKind = Literal[
    "downstream-services",
    "cloud-resources",
    "data-sources",
    "external-services",
]

# Union of every downstream kind's sortable fields, for MCP schema guidance.
# Per-kind validity is enforced in the tool (each kind allows only a subset).
DownstreamSortField = Literal[
    "serviceName",  # downstream-services
    "method",
    "route",
    "apiType",
    "name",  # cloud-resources + external-services
    "provider",
    "region",
    "type",
    "dbName",  # data-sources
    "hostname",
    "system",
    "domain",  # external-services
]

# kind -> (api path, default sort pairs, sortable fields)
DOWNSTREAM_KINDS: dict[str, tuple[str, list[tuple[str, str]], frozenset[str]]] = {
    "downstream-services": (
        "/v1/services/downstream-services",
        [("serviceName", "asc")],
        frozenset({"serviceName", "method", "route", "apiType"}),
    ),
    "cloud-resources": (
        "/v1/services/cloud-resources",
        [("name", "asc")],
        frozenset({"name", "provider", "region", "type"}),
    ),
    "data-sources": (
        "/v1/services/data-sources",
        [("dbName", "asc")],
        frozenset({"dbName", "hostname", "system"}),
    ),
    "external-services": (
        "/v1/services/external-services",
        [("domain", "asc")],
        frozenset({"domain", "name"}),
    ),
}

ALL_SORT_FIELDS = sorted(
    {
        *SERVICES_FIELDS,
        *ENDPOINT_FIELDS,
        *THIRD_PARTY_FIELDS,
        *FINDING_FIELDS,
        *VULNERABILITY_FIELDS,
        *DEPENDENCY_FIELDS,
        *DATA_SOURCE_FIELDS,
        *DATA_SOURCE_TABLE_FIELDS,
        *DOMAIN_FIELDS,
        *CLOUD_RESOURCE_FIELDS,
    }
)

__all__ = [
    "CLOUD_RESOURCE_DEFAULT_SORT",
    "CLOUD_RESOURCE_FIELDS",
    "CloudResourceField",
    "CloudResourceSortField",
    "DOMAIN_DEFAULT_SORT",
    "DOMAIN_FIELDS",
    "DomainEdgeProtection",
    "DomainField",
    "DomainSortField",
    "DATA_SOURCE_DEFAULT_SORT",
    "DATA_SOURCE_FIELDS",
    "DATA_SOURCE_TABLE_DEFAULT_SORT",
    "DATA_SOURCE_TABLE_FIELDS",
    "DataSourceField",
    "DataSourceSortField",
    "DataSourceTableField",
    "DataSourceTableSortField",
    "DEPENDENCY_DEFAULT_SORT",
    "DEPENDENCY_FIELDS",
    "DependencyField",
    "DOWNSTREAM_KINDS",
    "DownstreamKind",
    "DownstreamSortField",
    "ALL_SORT_FIELDS",
    "ENDPOINT_DEFAULT_SORT",
    "ENDPOINT_FIELDS",
    "EndpointField",
    "FINDING_DEFAULT_SORT",
    "FINDING_FIELDS",
    "FindingField",
    "FindingSeverity",
    "FindingStatus",
    "FindingType",
    "API_MAX_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "SERVICES_FIELDS",
    "ServiceField",
    "SortDirection",
    "THIRD_PARTY_DEFAULT_SORT",
    "THIRD_PARTY_FIELDS",
    "ThirdPartyField",
    "VULNERABILITY_DEFAULT_SORT",
    "VULNERABILITY_FIELDS",
    "VulnerabilityDependencyStatus",
    "VulnerabilityField",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
]
