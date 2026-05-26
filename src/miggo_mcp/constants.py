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

PulseCVEField = Literal[
    "id",
    "vulnId",
    "title",
    "severity",
    "epssScore",
    "isListedInKEV",
    "hasVulnerableFunctions",
    "hasRootCauseAnalysis",
    "hasVirtualPatch",
    "hasKnownExploits",
    "changeType",
    "publishedDate",
    "createdAt",
    "updatedAt",
]

PulseCVESeverity = Literal["critical", "high", "medium", "low", "info"]

CVEChangeType = Literal["NEW", "UPDATED", "NEW_EXPLOIT"]

PULSE_CVE_FIELDS = [
    "id",
    "vulnId",
    "title",
    "severity",
    "epssScore",
    "isListedInKEV",
    "hasVulnerableFunctions",
    "hasRootCauseAnalysis",
    "hasVirtualPatch",
    "hasKnownExploits",
    "changeType",
    "publishedDate",
    "createdAt",
    "updatedAt",
]

PULSE_CVE_DEFAULT_SORT = [("createdAt", "desc"), ("severity", "desc")]

ServiceDataSourceField = Literal[
    "id",
    "dbName",
    "hostname",
    "system",
    "serviceId",
]

SERVICE_DATA_SOURCE_FIELDS = [
    "id",
    "dbName",
    "hostname",
    "system",
    "serviceId",
]

SERVICE_DATA_SOURCE_DEFAULT_SORT = [("dbName", "asc")]

ServiceCloudResourceField = Literal[
    "id",
    "name",
    "provider",
    "region",
    "type",
    "serviceId",
]

SERVICE_CLOUD_RESOURCE_FIELDS = [
    "id",
    "name",
    "provider",
    "region",
    "type",
    "serviceId",
]

SERVICE_CLOUD_RESOURCE_DEFAULT_SORT = [("name", "asc")]

ServiceExternalServiceField = Literal[
    "id",
    "domain",
    "name",
    "iconName",
    "serviceId",
]

SERVICE_EXTERNAL_SERVICE_FIELDS = [
    "id",
    "domain",
    "name",
    "iconName",
    "serviceId",
]

SERVICE_EXTERNAL_SERVICE_DEFAULT_SORT = [("domain", "asc")]

ServiceDownstreamServiceField = Literal[
    "id",
    "method",
    "route",
    "serviceName",
    "apiType",
    "serviceId",
]

SERVICE_DOWNSTREAM_SERVICE_FIELDS = [
    "id",
    "method",
    "route",
    "serviceName",
    "apiType",
    "serviceId",
]

SERVICE_DOWNSTREAM_SERVICE_DEFAULT_SORT = [("serviceName", "asc")]

ALL_SORT_FIELDS = sorted(
    {
        *SERVICES_FIELDS,
        *ENDPOINT_FIELDS,
        *THIRD_PARTY_FIELDS,
        *FINDING_FIELDS,
        *VULNERABILITY_FIELDS,
        *DEPENDENCY_FIELDS,
        *PULSE_CVE_FIELDS,
        *SERVICE_DATA_SOURCE_FIELDS,
        *SERVICE_CLOUD_RESOURCE_FIELDS,
        *SERVICE_EXTERNAL_SERVICE_FIELDS,
        *SERVICE_DOWNSTREAM_SERVICE_FIELDS,
    }
)

__all__ = [
    "DEPENDENCY_DEFAULT_SORT",
    "DEPENDENCY_FIELDS",
    "DependencyField",
    "ALL_SORT_FIELDS",
    "CVEChangeType",
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
    "PULSE_CVE_DEFAULT_SORT",
    "PULSE_CVE_FIELDS",
    "PulseCVEField",
    "PulseCVESeverity",
    "SERVICES_FIELDS",
    "SERVICE_CLOUD_RESOURCE_DEFAULT_SORT",
    "SERVICE_CLOUD_RESOURCE_FIELDS",
    "SERVICE_DATA_SOURCE_DEFAULT_SORT",
    "SERVICE_DATA_SOURCE_FIELDS",
    "SERVICE_DOWNSTREAM_SERVICE_DEFAULT_SORT",
    "SERVICE_DOWNSTREAM_SERVICE_FIELDS",
    "SERVICE_EXTERNAL_SERVICE_DEFAULT_SORT",
    "SERVICE_EXTERNAL_SERVICE_FIELDS",
    "ServiceCloudResourceField",
    "ServiceDataSourceField",
    "ServiceDownstreamServiceField",
    "ServiceExternalServiceField",
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
