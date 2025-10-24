"""Utilities for normalizing Miggo API JSON envelopes."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping


def unwrap_envelope(payload: Mapping[str, Any]) -> tuple[Any, Mapping[str, Any]]:
    """Return ``(data, meta)`` from a standard Miggo API response."""
    data = payload.get("data")
    meta = payload.get("meta") or {}
    if not isinstance(meta, Mapping):
        meta = {}
    return data, meta


def collection_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Shape a list response with optional metadata."""
    data, meta = unwrap_envelope(payload)
    status = payload.get("status")
    response: dict[str, Any] = {"data": data}
    if meta:
        response["meta"] = meta
    if status is not None:
        response["status"] = status
    return response


def scalar_response(payload: Mapping[str, Any], key: str = "data") -> dict[str, Any]:
    """Return a normalized scalar payload (e.g., counts)."""
    return {key: payload.get(key)}


__all__ = ["collection_response", "scalar_response", "unwrap_envelope"]
