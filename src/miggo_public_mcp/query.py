"""Helpers for constructing Miggo API query strings."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

FilterInput = Mapping[str, Iterable[object] | object] | None
SortInput = Sequence[Sequence[str]] | None


def serialize_where(filters: FilterInput) -> dict[str, str]:
    """Translate filter mappings into Miggo's ``where.field=value1,value2`` syntax."""
    if not filters:
        return {}

    output: dict[str, str] = {}
    for field, values in filters.items():
        if values is None:
            continue

        normalized = _normalize_iterable(values)
        if not normalized:
            continue

        output[f"where.{field}"] = ",".join(_stringify(value) for value in normalized)

    return output


def serialize_sort(sort: SortInput) -> str | None:
    """Serialize a sequence of ``(field, direction)`` tuples into Miggo's format."""
    if not sort:
        return None

    flat: list[str] = []
    for pair in sort:
        if len(pair) != 2:
            raise ValueError("Sort tuples must contain exactly two elements")
        field, direction = pair
        flat.append(field)
        flat.append(direction)

    return ",".join(flat)


def compose_params(
    *,
    filters: FilterInput = None,
    skip: int | None = None,
    take: int | None = None,
    sort: SortInput = None,
    search: str | None = None,
    fields: Sequence[str] | None = None,
    extra: Mapping[str, object] | None = None,
) -> dict[str, str]:
    """Compose query parameters for Miggo endpoints."""
    params: dict[str, str] = {}

    params.update(serialize_where(filters))

    if skip is not None:
        params["skip"] = str(skip)
    if take is not None:
        params["take"] = str(take)

    sort_string = serialize_sort(sort)
    if sort_string:
        params["sort"] = sort_string

    if search:
        params["search"] = search

    if fields:
        params["fields"] = ",".join(fields)

    if extra:
        for key, value in extra.items():
            if value is None:
                continue
            params[key] = _stringify(value)

    return params


def _normalize_iterable(values: Iterable[object] | object) -> list[object]:
    """Return a list of values from user input ensuring iterables are flattened."""
    if isinstance(values, str | bytes):
        return [values]

    if isinstance(values, Iterable):
        return [item for item in values if item is not None]

    return [values]


def _stringify(value: object) -> str:
    """Convert Python values into strings acceptable by Miggo query parameters."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["compose_params", "serialize_sort", "serialize_where"]
