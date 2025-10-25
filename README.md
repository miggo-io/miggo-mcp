# Miggo Public FastMCP Server

This package ships a self-contained MCP stdio server that talks to Miggo's
[public API](https://api-beta.miggo.io), exposing services, endpoints,
third-parties, findings, vulnerabilities, and project metadata as static MCP
tools.

## Installation

```bash
uv pip install -e .
```

The project uses [uv](https://github.com/astral-sh/uv) for dependency
management, but any PEP 517 build frontend (e.g. `pip install .`) will work.

## Configuration

Export the following environment variables before launching the server:

| Variable | Required | Description |
| --- | --- | --- |
| `MIGGO_PUBLIC_API_URL` | No | Base URL of the Miggo public API. Defaults to `https://api-beta.miggo.io`. |
| `MIGGO_PUBLIC_TOKEN` | Yes | Bearer token issued by Miggo's authentication flow. |
| `MIGGO_PUBLIC_DEFAULT_TAKE` | Optional | Default page size for list endpoints (max 50). |
| `MIGGO_PUBLIC_DEFAULT_SKIP` | Optional | Default offset for list endpoints. |
| `MIGGO_PUBLIC_DEFAULT_SORT` | Optional | Default `field,direction` pairs (e.g. `risk,desc`). |

Settings are validated with `pydantic-settings`; misconfigured values raise a
concise error before the server starts.

## Usage

Launch the stdio server via the console script:

```bash
uv run miggo-public-mcp
```

or directly:

```bash
uv run python -m miggo_public_server.main
```

You can also run with the MCP inspector:

```bash
uv run mcp dev miggo_public_server/run.py  # run from the repository root
```

### Manual Smoke Test

With valid credentials:

```bash
export MIGGO_PUBLIC_TOKEN=...
uv run miggo-public-mcp
```

From another terminal or MCP client issue:

```bash
uv run python - <<'PY'
from mcp.client.stdio import StdioClient
from mcp.client.session import ClientSession

async def main():
    async with StdioClient.spawn(["uv", "run", "miggo-public-mcp"]) as client:
        async with ClientSession(client):
            result = await client.call_tool("services_count", {})
            print(result.content[0].text)

import asyncio
asyncio.run(main())
PY
```

### Available Tools

- `services_list`, `services_get`, `services_count`, `services_facets`
- `endpoints_list`, `endpoints_get`, `endpoints_count`, `endpoints_facets`
- `third_parties_list`, `third_parties_get`, `third_parties_count`, `third_parties_facets`
- `findings_list`, `findings_get`, `findings_count`, `findings_facets`
- `vulnerabilities_list`, `vulnerabilities_get`, `vulnerabilities_count`, `vulnerabilities_facets`
- `project_get`

### Tests

Run the async unit suite with:

```bash
uv run pytest
```

## Code Quality

Sync the development tooling before running local checks:

```bash
uv sync --extra dev
```

Format and lint the codebase with Ruff:

```bash
uv run --extra dev ruff format .
uv run --extra dev ruff check .
```

Install and exercise the pre-commit hooks to keep the repo clean:

```bash
uv run --extra dev pre-commit install
pre-commit run --all-files
```

Continuous integration runs in `.github/workflows/ci.yaml`, verifying `ruff format --check`, `ruff check`, and `pytest` on every push and pull request.

## Release Notes & Versioning

* Follow [SemVer](https://semver.org/) for the package version in `pyproject.toml`.
* Publish tagged releases via `uv publish` (or `hatch build` + `twine upload`).
* Update the change log (future `CHANGELOG.md`) prior to tagging a release.

## Future Work

1. Centralise response-model typing with Pydantic models for richer editor hints.
2. Explore streaming support for large result sets if the API introduces it.
