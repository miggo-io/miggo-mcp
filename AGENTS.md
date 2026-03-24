# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `src/miggo_mcp/`; `main.py` wires the FastMCP server, `client.py` wraps Miggo's API, and `tools/` registers each MCP tool.
- Settings and constants are isolated in `config.py` and `constants.py` to keep API details centralized.
- Async integration tests sit in `tests/`, mirroring module names (e.g., `test_client.py` covers `client.py`); use them as references for new scenarios.
- Support scripts such as `run.py` for launch helpers; `scripts/build.py` handles build and packaging; `docs/` holds reference materials.

## Build, Test, and Development Commands
```bash
# install with editable sources
uv pip install -e .
# format
uv run ruff format .
# lint
uv run ruff check .
# run tests
uv run pytest
# verify hooks locally
pre-commit run --all-files
```
Run commands from the repository root so relative imports and settings resolve correctly.

## Coding Style & Naming Conventions
- Target Python 3.12+, four-space indentation, and prefer typed function signatures.
- Keep modules cohesive: HTTP concerns in `client.py`, query assembly in `query.py`, response shaping in `response.py`.
- Name new tools with the `<resource>_<verb>` pattern used in `tools/__init__.py`.
- Before submitting, format new blocks with `python -m compileall src` to catch syntax drift if an auto-formatter is unavailable.

## Testing Guidelines
- Use `pytest` with `pytest-asyncio` fixtures; async tests should `await` client calls instead of blocking.
- Mirror production tool names in test function identifiers (e.g., `test_services_list_returns_items`) for quick traceability.
- Add integration stubs with `pytest-httpx` when calling out to Miggo to avoid live API calls.

## Commit & Pull Request Guidelines
- Follow Conventional Commit prefixes already in history (`feat:`, `fix(config):`, `docs:`) so changelog automation stays predictable.
- Squash or rebase before pushing to keep linear history; reference issue IDs in the commit body when applicable.
- PRs should describe scope, list verification steps (`uv run pytest`, smoke tests), and note required environment variables such as `MIGGO_PUBLIC_TOKEN`; include screenshots or JSON snippets when relevant to tool output.

## Configuration & Security Notes
- Never commit real tokens; rely on `.env` files that stay local. Document new settings in `README.md` and reference them from `config.py`.
- When extending API coverage, validate fields against `miggo-openapi.json` and update defaults in `constants.py` to keep behaviour predictable.

## CI & Automation
- GitHub Actions workflow `.github/workflows/ci.yaml` runs `uv sync --extra dev`, `ruff format --check`, `ruff check`, and `pytest` for every push and pull request.
