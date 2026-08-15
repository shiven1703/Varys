# Dependency Baseline

Status: Phase 0 complete. Every implementation increment must review the
affected dependency, toolchain, contract, and schema versions, and update this
document whenever a dependency or toolchain version changes.

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
| argon2-cffi | 25.1.0 | Argon2id password hashing for Phase 1 sessions. |
| FastAPI | 0.139.2 | HTTP application framework. |
| httpx | 0.28.1 | In-process HTTP testing support. |
| mypy | 1.15.0 | Static type checks. |
| pytest | 9.0.3 | Python test runner. |
| ruff | 0.9.10 | Formatting and linting. |
| psycopg | 3.2.4 | PostgreSQL database driver. |
| SQLAlchemy | 2.0.38 | Database engine and sessions. |
| Uvicorn | 0.34.0 | ASGI process server. |

FastAPI `0.139.2`, Starlette `1.3.1`, Mako `1.3.12`, and pytest `9.0.3`
replace the vulnerable Phase 0 pins reported by `pip-audit`; their newly
required `annotated-doc` and `Pygments` transitive pins are retained in
`requirements-dev.lock`.

Iteration 0D adds FastAPI and Uvicorn for the inert API/worker bootstrap;
Iteration 0E adds the PostgreSQL stack. Storage uses the standard library. The
Iteration 0H image uses Python `3.12.13-slim-bookworm` and Node
`24.18.0-bookworm-slim`, applies Debian security upgrades, then installs the
exact Python pins from `requirements-dev.lock`. It also pins container-only
`pip==26.2.1`, `setuptools==78.1.1`, and `wheel==0.46.2` to resolve Trivy's
reported packaging-tool findings, then removes `setuptools` and `wheel` from
the final runtime image because the application does not require build tooling.
The project requires Python `>=3.12,<3.13`. Transitive pins are retained in
`requirements-dev.lock`.

Iteration 1A adds `argon2-cffi==25.1.0` with its pinned
`argon2-cffi-bindings==25.1.0`, `cffi==2.1.1`, and `pycparser==3.0`
transitives. No contract, output-schema, parser-format, or API-version change
was required: the new JSON endpoints use the locked `/api/v1` namespace.

Iteration 1B adds no dependency or toolchain version. It advances the Alembic
schema head from `0002_authentication` to `0003_run_dispatch`; all API,
contract, output-schema, and parser-format versions remain unchanged.

Docker Buildx `0.36.1` already supports the BuildKit cache-mount syntax used by
the application Dockerfile. The Docker build now keeps npm and pip download
caches outside the final image, so no dependency or lockfile change is needed.

Iteration 1C uses only the Python standard library and existing pinned
dependencies. No dependency, toolchain, API, output-schema, parser-format, or
contract version changes are required.

## Frontend dependencies

`frontend/package-lock.json` records the complete npm dependency graph. The
direct Phase 0G/0I pins are Angular `21.2.20`, Angular CLI/build `21.2.21`,
TypeScript `5.9.3`, PrimeNG `21.1.9`, AG Grid Community `35.3.1`, Vitest
`4.1.10`, jsdom `29.1.1`, Playwright `1.52.0`, ESLint `9.24.0`, and
typescript-eslint `8.48.0`. Angular 21 is selected because it supports the
available Node 24.0 host; Angular 22 requires Node 24.15 or later. CI installs
the separate pinned `pip-audit==2.9.0` scanner rather than making it an
application dependency.
