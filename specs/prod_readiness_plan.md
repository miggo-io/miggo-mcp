# Prod Readiness Plan: Ruff Guardrails & CI

## 1. Establish Ruff As The Formatting/Linting Source Of Truth
- [ ] Confirm `pyproject.toml` includes a `[tool.ruff]` section with project-appropriate settings; add or update it to cover formatting (`format`) and linting (`lint.select`, `lint.ignore`).
- [ ] Add `ruff` (and supporting CLI tooling) to `[project.optional-dependencies.dev]` so the project follows standard PyPA configuration while keeping developer tooling isolated from runtime dependencies; pin a compatible version to keep CI reproducible.
- [ ] Run `uv run ruff format .` and `uv run ruff check .` locally to baseline any formatting changes and lint violations; capture and address fixes in follow-up commits before locking automation in place.

## 2. Wire Ruff Into Pre-commit Hooks
- [ ] Add `pre-commit` as a dev dependency and document the bootstrap command (`uv run pre-commit install`).
- [ ] Create or update `.pre-commit-config.yaml` with `ruff` hooks for `ruff-format` and `ruff` (lint), scoping them to Python sources under `src/` and `tests/`.
- [ ] Use `repo: local` entries so the hooks reuse the repo's `ruff` install (e.g., `entry: uv run ruff format`).
- [ ] Run `uv run pre-commit run --all-files` to ensure the hook chain succeeds and leaves the working tree clean; document this as the recommended verification step before committing.

## 3. Enforce Ruff & Tests In GitHub Actions
- [ ] Create `.github/workflows/ci.yaml` (or extend an existing workflow) triggered on `pull_request` and pushes to main branches.
- [ ] Configure a single Python 3.12 job that checks out the repo, installs dependencies via `uv sync --all-extras` (or equivalent), and caches the `.venv/.uv` directory for faster runs.
- [ ] Add sequential steps for `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest`; fail fast on any violations.
- [ ] Publish workflow status badges/documentation in `README.md` so contributors know CI expectations.

## 4. Communicate & Roll Out
- [ ] Update `README.md` and `AGENTS.md` with the expected local commands and CI checks so contributors stay aligned.
- [ ] Encourage contributors to re-run `uv run pre-commit install` after pulling changes so hooks activate.
- [ ] Monitor the first few CI runs to ensure cache paths and `uv` commands behave; adjust as needed (e.g., add platform matrix later).
- [ ] Capture lessons learned and backlog follow-ups (type-checking, security scans) for future tightening of prod readiness.
