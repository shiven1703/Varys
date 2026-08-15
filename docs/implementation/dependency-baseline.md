# Dependency Baseline

Status: Phase 0 Iteration 0C. Update this document with each dependency or
toolchain change.

## Host prerequisites

| Tool | Verified version | Purpose |
| --- | --- | --- |
| Python | 3.12.3 | Creates the repository-local virtual environment. |
| pip | 24.0 | Installs pinned project tooling into `.venv`. |
| GNU Make | 4.3 | Stable developer command interface. |
| Git | 2.43.0 | Source control. |
| ripgrep | 14.1.0 | Repository search. |
| Node.js | 24.0.0 | Builds and tests the Angular workspace. |
| npm | 11.3.0 | Installs the pinned frontend workspace. |
| Docker Compose | 5.4.0 | Builds and runs the local runtime topology. |

`uv` is not a host prerequisite. `make bootstrap` creates `.venv` and installs
the exact pins in `requirements-dev.lock` there, so check commands use no global
Python packages. It retains the venv-provided pip and does not upgrade it.

## Pinned development dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| setuptools | 75.8.0 | Editable project installation backend. |
| Alembic | 1.14.1 | PostgreSQL migration management. |
| FastAPI | 0.115.12 | HTTP application framework. |
| httpx | 0.28.1 | In-process HTTP testing support. |
| mypy | 1.15.0 | Static type checks. |
| pytest | 8.3.5 | Python test runner. |
| ruff | 0.9.10 | Formatting and linting. |
| psycopg | 3.2.4 | PostgreSQL database driver. |
| SQLAlchemy | 2.0.38 | Database engine and sessions. |
| Uvicorn | 0.34.0 | ASGI process server. |

Iteration 0D adds FastAPI and Uvicorn for the inert API/worker bootstrap;
Iteration 0E adds the PostgreSQL stack. Storage uses the standard library. The
Iteration 0H image uses Python `3.12.3-slim-bookworm` and Node
`24.0.0-bookworm-slim`, then installs the exact Python pins from
`requirements-dev.lock`. The project requires Python `>=3.12,<3.13`.
Transitive pins are retained in `requirements-dev.lock`.

## Frontend dependencies

`frontend/package-lock.json` records the complete npm dependency graph. The
direct Phase 0G pins are Angular `21.2.20`, Angular CLI/build `21.2.21`,
TypeScript `5.9.3`, PrimeNG `21.1.9`, AG Grid Community `35.3.1`, Vitest
`4.1.10`, and jsdom `29.1.1`. Angular 21 is selected because it supports the
available Node 24.0 host; Angular 22 requires Node 24.15 or later.
