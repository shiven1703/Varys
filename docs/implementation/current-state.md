# Varys Current State

Last updated: 2026-08-15

## Repository commit

Phase 0 starting commit: `27d0fea59b79086af589350c36d26ab70bc58854`

The Pre-Phase bootstrap was committed on `main` as `c20b416`; the temporary
Codex configuration was deliberately removed in `27d0fea`. The working tree
was clean when Phase 0 began.

## Approved phases

- Pre-Phase — approved by the owner on 2026-08-15.

## Current phase and status

Phase 0: `IN_PROGRESS` — Iteration 0B
Implementation plan revision: 3

Pre-Phase is approved. Phase 0 is authorized to start in a new Codex chat but
is not itself approved.

## Implemented capabilities

- No application capabilities are implemented.
- The Ubuntu development host and repository governance baseline are prepared.
- Pre-Phase acceptance passed on 2026-08-15.
- Docker Engine, Buildx, Compose, Codex, Git, and required host CLI tools are
  installed and verified.
- The three approved planning/source documents named by the implementation plan
  are present under `docs/implementation/` for Phase 0 contract work.

## Not implemented

- All Phase 0 through Phase 7 application work.
- Application source code, dependency manifests, database migrations, runtime
  images, Compose topology, tests, and CI.

## Known failing tests

No application test suite exists yet.

## Known limitations

- A login/session restart is required before Phase 0 if the user has not yet
  started a fresh session since Docker-group membership was added.
- `/home/shivam/.profile` contains a stale VS Code environment source at line
  29. It emits a warning for login shells but does not block project commands.

## Open risks

- Docker client access is unavailable in the current Codex session because it
  has not inherited Docker-group membership. The owner accepted deferring this
  validation; it remains required for the later Compose increment.
- Host resources are suitable for bootstrap, but later image builds should be
  monitored on this 7.2 GiB RAM development machine.
- No unresolved cross-document contradiction is known after the 2026-08-15
  planning alignment audit. Phase 0 must still surface any new ambiguity found
  while turning the approved baselines into exact versioned contracts.

## Planning alignment review

Completed on 2026-08-15 across the product/architecture specification, both
historical handoffs, implementation plan, `AGENTS.md`, phase state files, and
the Phase 0 new-chat handover.

Resolved and recorded:

- `main` is the default working branch through the first V1 release; a temporary
  branch is used only when the owner explicitly requests one for a specific
  risk, experiment, or review boundary. The full check suite remains mandatory.
- The product specification's index minimum wins: the contract must include
  `volume_or_shares_traded_if_available` and `turnover_if_available` with
  canonical `NA` behavior when unavailable.
- JSON APIs use `/api/v1/*`; authenticated binary downloads use `/files/*`.
- Phase 0 Iteration 0J makes repository state documents the complete progress
  and acceptance ledger.
- Phase 0's ten outcomes and Phase 1's eight outcomes are mapped explicitly to
  the implementation plan's finer-grained iterations.
- Repository state is the source of truth for implementation progress.

## Current database migration revision

Not applicable; Alembic is not initialized.

## Current output schema versions

- CSV representation: `v1`
- Equity CSV: `v1`
- Index CSV: `v1`
- Universe CSV: `v1`
- Manifest: `v1`
- Preparation report: `v1`

## Current Docker/runtime topology

Docker Engine is installed on the host. No Varys image, Compose file, service,
volume, or network exists.

## Git workflow

- Use `main` as the default working branch through the first V1 release.
- Create or switch to a temporary branch only when the owner explicitly
  requests one for a specific risk, experiment, or review boundary.
- Use small, coherent, verified commits as review and rollback checkpoints.
- Phase approval remains owner-controlled and is independent of Git branching.

## Current developer commands

Pre-Phase host checks are documented in the implementation plan. Stable project
commands will be created in Phase 0 Iteration 0C.

## Decisions due before later phases

- Phase 0 must lock all contracts listed in plan section 8.1 before Phase 1.
- Phase 0 must lock the exact index/universe schemas and optional-value
  semantics from the minimum approved baselines in plan sections 9.4 and 9.5.
- Live NSE discovery details are due before Phase 2.
- Production backup transport and Cloudflare settings are due before Phase 6.

## Next allowed implementation work

Begin Iteration 0B architecture and repository-boundary documentation. Do not
start Phase 1 work.
