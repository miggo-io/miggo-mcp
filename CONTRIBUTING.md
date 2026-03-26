# Contributing to Miggo MCP Server

Thanks for your interest in contributing! This document covers the process for submitting issues and pull requests.

## Reporting issues

- Search [existing issues](https://github.com/miggo-io/miggo-mcp/issues) before opening a new one.
- Include steps to reproduce, expected vs. actual behavior, and any relevant logs.

## Pull requests

1. **Fork** the repository and create a branch from `main`.
2. **Install** dependencies: `uv sync --dev`
3. **Make your changes** — keep the scope focused on a single concern.
4. **Add or update tests** if your change affects behavior.
5. **Run the checks** before pushing:
   ```bash
   uv run pytest
   uv run ruff format .
   uv run ruff check .
   ```
6. **Open a pull request** against `main` with a clear description of what and why.

## Scope

This MCP server is intentionally focused on read-only queries against Miggo's public API. Contributions that fit well:

- New query filters, sort fields, or facet options
- Improved error messages and edge-case handling
- Documentation fixes and improvements
- Performance improvements to pagination or caching
- Support for new MCP client integrations

Out of scope (for now):

- Write/mutation operations against the Miggo API
- Authentication flow changes (these are tightly coupled to the Miggo backend)

## Code style

- **Formatter/linter**: [Ruff](https://docs.astral.sh/ruff/) — enforced in CI
- **Type hints**: Use them everywhere; `Literal` types for constrained values
- **Tests**: [pytest](https://docs.pytest.org/) with `pytest-asyncio` for async tests
- **Pre-commit**: Run `uv run pre-commit install` to set up hooks locally

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
