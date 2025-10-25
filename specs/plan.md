# Plan: Public Miggo FastMCP Server

## Objectives
- Stand up a brand-new `FastMCP` stdio server that talks to Miggo's public API (`https://api-beta.miggo.io`).
- Bake the MCP tool definitions directly into the codebase (no runtime spec parsing), starting with the public `services` endpoints described in `miggo-openapi.json`.
- Package the new server independently so it can evolve, version, and ship on its own timeline.
- Document authentication and configuration expectations clearly for users of the public API.

## Step-by-step Plan

1. **Scope & Requirements Review**
   - Read the `miggo-openapi.json` sections for the `services` tag to manual-map endpoints (`/v1/services/`, `/v1/services/{id}`, `/v1/services/count`, `/v1/services/facets`, etc.), their parameters, and expected responses.
   - Capture public API authentication expectations (JWT bearer token via `auth` scheme) and note any required headers beyond what the spec states.

2. **Isolated Package Skeleton**
   - Create a fresh package directory at the repository root (e.g., `miggo_public_server/`).
   - Add its own `pyproject.toml` (or `uv` project metadata) declaring dependencies (`mcp[cli]`, `httpx`, testing stack) so it can be built and distributed separately.
   - Provide an entry script (`scripts/run_public_mcp.py` or similar) that invokes the package’s main module via `uv run`.

3. **Configuration & Bootstrap**
   - Implement a small configuration module that loads required env vars (`MIGGO_PUBLIC_API_URL`, `MIGGO_PUBLIC_TOKEN`, optional paging defaults) with clear error messaging when unset.
   - Wire up the package’s `__main__` / `main.py` to initialize `FastMCP` with a distinct server name, load configuration, and register all services tools.
   - Ensure the bootstrap is self-contained so the new server can be installed and executed on its own.

4. **API Client Layer**
   - Create an async `httpx` client wrapper that injects bearer token headers, handles optional query params (`skip`, `take`, `sort`), and logs/raises errors in a consistent manner.
   - Add helpers that translate ergonomic tool arguments into the Miggo `where.field=value1,value2` query string pattern expected by the public endpoints.
   - Expose reusable response-shaping utilities (e.g., optional pagination metadata extraction) to keep the MCP tools lean.

5. **Author Services MCP Tools**
   - For each services endpoint identified earlier, define a strongly-typed MCP tool coroutine with docstrings summarizing purpose, arguments, and illustrative response fields.
   - Validate inputs (booleans, enums, numeric ranges) before dispatching requests to provide fast feedback from within the MCP environment.
   - Register each tool with descriptive names (`services_list`, `services_get`, `services_count`, `services_facets`) and ensure consistent output structure (return raw JSON data plus helpful metadata where appropriate).
   - Keep these definitions static—any future schema changes will be handled by updating the Python code, not by dynamic spec parsing.

6. **Quality & Testing**
   - Add async unit tests using `pytest` and `respx` (or `pytest-httpx`) to stub Miggo responses, covering happy paths, parameter serialization, and error handling for every services tool.
   - Provide a manual smoke-test recipe (env vars + `uv run miggo_public_server/main.py` + CLI tool invocations) to verify real API communication when credentials are available.

7. **Documentation & Release Prep**
   - Document installation, configuration, and usage in a new `README.md` scoped to the public server package, highlighting any public-API-specific constraints.
   - Record follow-up tasks for additional endpoint families (e.g., vulnerabilities) once services support is stable, outlining how to extend the new client/tool structure.
   - Define a versioning/release strategy for the separate package, including any publishing steps or integration instructions for downstream consumers.
