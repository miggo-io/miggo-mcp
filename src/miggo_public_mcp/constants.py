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

ALL_SORT_FIELDS = sorted(
    {
        *SERVICES_FIELDS,
        *ENDPOINT_FIELDS,
        *THIRD_PARTY_FIELDS,
        *FINDING_FIELDS,
        *VULNERABILITY_FIELDS,
    }
)

__all__ = [
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
