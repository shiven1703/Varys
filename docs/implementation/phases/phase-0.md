# Phase 0 State

Status: IN_PROGRESS
Owner approved: no
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
- Iteration 0E: IN_PROGRESS
- Iteration 0F: NOT_STARTED
- Iteration 0G: NOT_STARTED
- Iteration 0H: NOT_STARTED
- Iteration 0I: NOT_STARTED
- Iteration 0J: NOT_STARTED

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

## Deviations from plan

- The owner selected `main` as the default through the first V1 release. A
  temporary branch is used only when explicitly requested for a specific risk,
  experiment, or review boundary. Phase status and owner-approval gates remain
  unchanged.

## Known limitations

- The bootstrap has no database, storage, scheduler, or production runtime yet.
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

- Begin Iteration 0E PostgreSQL and Alembic foundations.

## Owner approval

Phase 0 is not approved. Pre-Phase approval authorizes Phase 0 to start, but
only the owner may approve Phase 0 after its full acceptance suite passes.
