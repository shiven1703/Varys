# Phase 0 State

Status: APPROVED
Owner approved: yes (2026-08-15)
Plan revision: 3
Started from commit: `27d0fea59b79086af589350c36d26ab70bc58854`
Current commit: Resolve with `git rev-parse HEAD` before each evidence update

## Objective

Create the reproducible contracts, architecture boundaries, backend/worker and
database foundations, safe storage primitives, Angular shell, shared Docker
runtime, Compose topology, tests, CI, and repository state documentation needed
for the Phase 1 fixture-based vertical slice.

## Scope

- Iteration 0A: versioned data, package, state, adapter, API, configuration, and
  filesystem contracts.
- Iteration 0B: repository/module/runtime architecture and initial ADRs.
- Iteration 0C: Python project tooling and stable developer commands.
- Iteration 0D: independent FastAPI and worker bootstraps.
- Iteration 0E: PostgreSQL, SQLAlchemy, Alembic, and readiness foundations.
- Iteration 0F: safe and durable filesystem primitives.
- Iteration 0G: Angular standalone application shell.
- Iteration 0H: one application image and local Compose topology.
- Iteration 0I: deterministic test and CI foundations.
- Iteration 0J: Codex workflow and repository implementation-state
  documentation.

## Out of scope

- Phase 1 authentication, run persistence, fixture adapters/parsers, package
  generation, download APIs, daily UI, and vertical-slice E2E behavior.
- Live NSE access or acquisition logic.
- Production scheduling, backfill, repair, deployment, and release hardening.
- Any infrastructure excluded by the locked V1 architecture.

## Implementation iterations

- Iteration 0A: COMPLETED
- Iteration 0B: COMPLETED
- Iteration 0C: COMPLETED
- Iteration 0D: COMPLETED
- Iteration 0E: COMPLETED
- Iteration 0F: COMPLETED
- Iteration 0G: COMPLETED
- Iteration 0H: COMPLETED
- Iteration 0I: COMPLETED
- Iteration 0J: COMPLETED

## Acceptance criteria

Sections 10.2 through 10.12 of
`docs/implementation/implementation-plan.md` are authoritative.

## Acceptance evidence

Phase 0 started on the clean `main` working tree at
`27d0fea59b79086af589350c36d26ab70bc58854`. The documented uncommitted
bootstrap baseline had already been committed as `c20b416`; `27d0fea`
deliberately removed its temporary Codex configuration.

Iteration 0A contract review passed: all twelve required `v1` contracts exist;
the exact equity, index, and universe schemas are locked; state, package,
adapter, API, configuration, filesystem, numeric, newline, and ordering rules
are explicit. Deterministic checks verified the file inventory, contract
versions, required index and universe headers, API/download split, required
state names, and `git diff --check`.

The owner accepted Iteration 0A on 2026-08-15. This acceptance does not approve
Phase 0; the phase remains `IN_PROGRESS` until its complete acceptance suite
passes and the owner explicitly approves the phase.

Iteration 0B architecture review passed: repository structure, module
boundaries, and runtime topology explicitly preserve one Python codebase and
one application image for app/worker, PostgreSQL-backed dispatch, no broker or
microservice split, no Nginx, and the filesystem/database publication boundary.
ADRs record the run-dispatch and recoverable package-publication decisions.
`git diff --check` and targeted deterministic content checks passed.

The owner accepted Iteration 0B on 2026-08-15. This acceptance does not approve
Phase 0; the phase remains `IN_PROGRESS` until its complete acceptance suite
passes and the owner explicitly approves the phase.

Iteration 0C tooling review passed. `make bootstrap` created `.venv` and
installed the exact pins in `requirements-dev.lock`; `make format` left the
tooling test unchanged; `make check` passed Ruff, mypy, and one pytest unit
test. The stable root command surface is documented in `README.md`; commands
owned by later iterations are explicit placeholders.

The owner accepted Iteration 0C on 2026-08-15. This acceptance does not approve
Phase 0; the phase remains `IN_PROGRESS` until its complete acceptance suite
passes and the owner explicitly approves the phase.

Iteration 0D bootstrap review passed. The shared configuration loader rejects
unknown `VARYS_` settings and validates bootstrap values; app and worker emit
structured JSON logs with request context and secret redaction. The FastAPI app
serves `/api/health/live` (and its versioned alias) with `200 {"status":"ok"}`;
the API and worker both pass independent `python -m ... --check` process tests.
No worker work runs in the app process. `make check` passed 7 unit tests, Ruff,
and mypy.

The owner accepted Iteration 0D on 2026-08-15. This acceptance does not approve
Phase 0; the phase remains `IN_PROGRESS` until its complete acceptance suite
passes and the owner explicitly approves the phase.

Iteration 0E is implemented but not yet acceptance-complete. SQLAlchemy uses
PostgreSQL-only URLs; Alembic head is `0001_database_foundation` with no
speculative tables; readiness rejects missing, unreachable, and revision-skewed
databases. `make check` passed 10 unit tests, Ruff, and mypy. The PostgreSQL
integration harness skips without `VARYS_TEST_DATABASE_URL`, so clean-database
migration and live readiness evidence remain pending the approved Docker/test
database access. The expanded unit suite passes 12 tests.

The owner accepted Iteration 0E on 2026-08-15. This acceptance does not approve
Phase 0. The pending clean-PostgreSQL integration evidence remains recorded and
must be completed before Phase 0 acceptance.

Iteration 0F filesystem review passed. Storage paths reject traversal, malformed
identifiers, and symlink escape; durable writes remain `.part` files until a
same-filesystem atomic publish; SHA-256 output is fixed by test; and readiness
detects missing or unwritable storage roots. `/api/health/ready` now combines
database and storage readiness. `make check` passed 16 unit tests, Ruff, and
mypy.

The owner accepted Iteration 0F on 2026-08-15. This acceptance does not approve
Phase 0. The pending clean-PostgreSQL integration evidence remains required
before Phase 0 acceptance.

Iteration 0G Angular review passed. The standalone shell provides the six
approved route placeholders without fake market or run data, a PrimeNG baseline,
an AG Grid Community dependency for future dense views, and an environment-
relative API client foundation. `npm run build` completed and `npm test` passed
the route-placeholder component test. FastAPI hosting of the bundle remains
deferred to Iteration 0H.

The owner accepted Iteration 0G on 2026-08-15. This acceptance does not approve
Phase 0. The pending clean-PostgreSQL integration evidence remains required
before Phase 0 acceptance.

Iteration 0H implementation added a multi-stage Docker image that produces the
Angular bundle and the shared Python runtime image, plus a Compose topology
with app, worker, internal PostgreSQL, named data volumes, and an optional
disabled-by-default cloudflared profile. FastAPI serves the copied Angular
bundle at `/`; API and file namespaces remain reserved. `make check` passed 17
unit tests, Ruff, and mypy; the Angular production build and frontend test
passed; and `docker compose config --quiet` passed with a supplied local test
password. Docker build/up/smoke execution remains deferred because this Codex
session cannot access the Docker daemon.

The owner accepted Iteration 0H on 2026-08-15. This acceptance does not approve
Phase 0. Docker build/up/smoke evidence and the pending clean-PostgreSQL
integration evidence remain required before Phase 0 acceptance.

Iteration 0I implementation added executable pytest golden and
failure-injection layers, an autouse normal-test network prohibition with a
proving unit test, frontend ESLint, a Playwright app-shell smoke skeleton, and
main-only GitHub Actions jobs for Python, frontend, E2E, Compose smoke,
dependency, and image scanning. `make format`, `make check` (18 unit tests),
`make test-golden`, and `make test-failure-injection` passed. The PostgreSQL
integration test correctly skipped without `VARYS_TEST_DATABASE_URL`; frontend
lint, production build, unit test, and Playwright test discovery passed.
`docker compose config --quiet` and the production npm audit passed. Docker
execution, Playwright browser execution, pip-audit, Trivy, and remote GitHub
Actions evidence remain pending their Docker/CI environments.

The owner accepted Iteration 0I on 2026-08-15. This acceptance does not approve
Phase 0. Docker, browser, scanner, clean-PostgreSQL integration, and remote CI
evidence remain required before Phase 0 acceptance.

Iteration 0J added the AI session entrypoint and workflow documents, a factual
risk register, a definition-of-done ledger, and a deterministic documentation
presence check. The repository remains in `IN_PROGRESS`: the missing Docker,
browser, scanner, clean-PostgreSQL, and remote-CI acceptance evidence is not
represented as passed.

The owner accepted Iteration 0J on 2026-08-15. This acceptance does not approve
Phase 0. A tracked-file and reachable-history public-repository audit found no
high-confidence credentials or private keys; Gitleaks now scans full history in
CI. At that checkpoint, Phase 0 remained `IN_PROGRESS` until its Docker,
browser, scanner, clean-PostgreSQL, and remote-CI acceptance evidence was
complete.

CI remediation after the first remote run corrected the Trivy action reference
to `v0.36.0`, made the worker remain alive until shutdown, built app once then
started app and worker from their shared image, and consolidated all checks into
one sequential job that reuses the Compose image for smoke, Playwright, and
Trivy. FastAPI `0.139.2`, Starlette `1.3.1`, Mako `1.3.12`, and pytest
`9.0.3` resolve the reported pip-audit findings. Local `make check` passed 19
unit tests; golden and failure tests, frontend lint/build/unit tests, Playwright
discovery, `pip-audit`, Compose configuration, and shell syntax passed. Docker
runtime and remote CI validation remain pending.

A follow-up remote `make check` failure showed that Compose-only `VARYS_`
variables had been exported to every CI step. Those variables now apply only to
the Compose smoke step; local `make check` again passes 19 unit tests while the
strict unknown-setting guard remains unchanged.

The subsequent Compose smoke failure was traced to `app.sh` invoking Alembic
without passing `VARYS_DATABASE_URL`, so the app exited before its liveness
health check. The entrypoint now uses the existing validated
`upgrade_database()` helper, and smoke cleanup prints service logs on a future
failure before removing containers.

Trivy then reported fixed HIGH/CRITICAL findings in the two-year-old runtime
base and its bundled packaging tools. The Docker image now uses current pinned
Python/Node Bookworm bases, applies Debian upgrades, and pins secure container
packaging tools. A later scan confirmed the Debian base has zero findings, but
reported vulnerable metadata vendored inside `setuptools`; `setuptools` and
`wheel` are now removed after dependency installation because neither is needed
at runtime. A further scan still reported two findings for packages absent from
the final package inventory and warned that its third-party SBOM can be
inaccurate; `.trivyignore` suppresses only those IDs until 2026-09-15 while the
HIGH/CRITICAL gate remains enabled. Trivy scans image vulnerabilities only;
full-history Gitleaks remains the separate secret scanner.

The owner reported that all required GitHub Actions CI checks passed on
2026-08-15, including the Docker Compose smoke, clean PostgreSQL migration and
integration path, Playwright smoke, dependency audits, and Trivy image scan.
The owner then explicitly approved Phase 0. This completes the Phase 0
acceptance suite and authorizes Phase 1 Iteration 1A.

## Deviations from plan

- The owner selected `main` as the default through the first V1 release. A
  temporary branch is used only when explicitly requested for a specific risk,
  experiment, or review boundary. Phase status and owner-approval gates remain
  unchanged.

## Known limitations

- Local Docker execution remains unavailable to this Codex session; successful
  main CI provides the required Phase 0 Docker and PostgreSQL evidence.
- The bootstrap has no scheduler or production runtime yet.
- The three higher-authority planning inputs are now materialized as the
  versioned Iteration 0A contracts.

## Risks opened/closed

- Closed: the owner added all three planning inputs named in section 2 of the
  implementation plan.
- Closed: the 2026-08-15 planning audit reconciled the known Git workflow,
  index-turnover, API/download-path, progress-ledger, and Phase 0/1 iteration
  mapping inconsistencies.
- Closed: the approved minimum baselines have been translated into exact
  versioned contracts for the Phase 1 fixture slice.
- Open: monitor memory use during container and frontend builds on the 7.2 GiB
  RAM development host.

## Decisions/ADRs created

- `ADR-001-postgresql-run-dispatch.md`
- `ADR-002-package-publication.md`

## Next actions

- Begin only Phase 1 Iteration 1A using the Phase 1 handover and state files.
- Review and update relevant dependency, toolchain, contract, and schema
  versions in every Phase 1 increment.

## Owner approval

The owner explicitly approved Phase 0 on 2026-08-15 after the full CI suite
passed. Phase 1 may begin, but only the owner may approve Phase 1 after its
full acceptance suite passes.
