# Phase 0 State

Status: NOT_STARTED
Owner approved: no
Plan revision: 3
Started from commit: N/A
Current commit: Resolve with `git rev-parse HEAD` at Phase 0 startup

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

- Iteration 0A: NOT_STARTED
- Iteration 0B: NOT_STARTED
- Iteration 0C: NOT_STARTED
- Iteration 0D: NOT_STARTED
- Iteration 0E: NOT_STARTED
- Iteration 0F: NOT_STARTED
- Iteration 0G: NOT_STARTED
- Iteration 0H: NOT_STARTED
- Iteration 0I: NOT_STARTED
- Iteration 0J: NOT_STARTED

## Acceptance criteria

Sections 10.2 through 10.12 of
`docs/implementation/implementation-plan.md` are authoritative.

## Acceptance evidence

None. Phase 0 has not started.

## Deviations from plan

- The owner selected `main` as the default through the first V1 release. A
  temporary branch is used only when explicitly requested for a specific risk,
  experiment, or review boundary. Phase status and owner-approval gates remain
  unchanged.

## Known limitations

- No application project, tests, contracts, ADRs, or Phase 0 runtime exist yet.
- The three higher-authority planning inputs are now present under
  `docs/implementation/` and passed a cross-document planning audit, but have
  not yet been materialized into the versioned Phase 0 contracts.

## Risks opened/closed

- Closed: the owner added all three planning inputs named in section 2 of the
  implementation plan.
- Closed: the 2026-08-15 planning audit reconciled the known Git workflow,
  index-turnover, API/download-path, progress-ledger, and Phase 0/1 iteration
  mapping inconsistencies.
- Open: surface and resolve any new ambiguity found while translating approved
  minimum baselines into exact versioned contracts.
- Open: monitor memory use during container and frontend builds on the 7.2 GiB
  RAM development host.

## Decisions/ADRs created

None. Initial ADRs belong to Iteration 0B.

## Next actions

- Start a fresh Codex chat with `docs/implementation/handoffs/phase-0.md`.
- Verify `main`, the exact commit, the documented uncommitted bootstrap files,
  Docker access, and all required source documents.
- Request permission to create the bootstrap baseline commit before application
  implementation begins.
- Report the mandatory Phase 0 baseline before editing.
- Transition to `IN_PROGRESS` only when implementation actually begins.
- Implement Iteration 0A first and verify it before proceeding iteratively.

## Owner approval

Phase 0 is not approved. Pre-Phase approval authorizes Phase 0 to start, but
only the owner may approve Phase 0 after its full acceptance suite passes.
