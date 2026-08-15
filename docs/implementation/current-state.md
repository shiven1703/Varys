# Varys Current State

Last updated: 2026-08-15

## Repository commit

Phase 0 starting commit: `27d0fea59b79086af589350c36d26ab70bc58854`

The Pre-Phase bootstrap was committed on `main` as `c20b416`; the temporary
Codex configuration was deliberately removed in `27d0fea`. The working tree
was clean when Phase 0 began.

## Approved phases

- Pre-Phase — approved by the owner on 2026-08-15.
- Phase 0 — approved by the owner on 2026-08-15 after all required CI checks
  passed.

## Current phase and status

Phase 1: `IN_PROGRESS` — Phase 0 and the Iteration 1A authentication increment
are owner-accepted; Iterations 1B run dispatch and 1C fixture adapters and
workspaces were owner-accepted on 2026-08-15. Iteration 1D parsers and
canonical writers are in progress.
Implementation plan revision: 3

Phase 1 continues through owner-accepted scoped increments. Its owner approval
remains pending until the Phase 1 acceptance suite passes.

## Implemented capabilities

- The Ubuntu development host and repository governance baseline are prepared.
- Pre-Phase acceptance passed on 2026-08-15.
- Docker Engine, Buildx, Compose, Codex, Git, and required host CLI tools are
  installed and verified.
- The three approved planning/source documents named by the implementation plan
  are present under `docs/implementation/` for Phase 0 contract work.
- A repository-local Python toolchain, pinned development dependency lock, and
  stable root developer commands are implemented and verified.
- The FastAPI and dedicated worker boot independently from shared Python code;
  validated startup configuration, structured JSON logging, request IDs, and
  the liveness endpoint are implemented.
- PostgreSQL-only SQLAlchemy sessions, Alembic configuration, migration head
  `0001_database_foundation`, database readiness checks, and an integration
  test harness are implemented.
- Safe storage-root resolution, SHA-256 hashing, durable `.part` writes,
  same-filesystem atomic publication, directory sync, and storage readiness
  checks are implemented.
- An Angular standalone shell with the six approved empty-state routes, PrimeNG
  baseline, AG Grid Community dependency, environment-relative API client, and
  component test is implemented.
- A multi-stage application image, FastAPI-served Angular bundle, shared
  app/worker image, local Compose topology, and Compose smoke workflow are
  implemented.
- Pytest unit, integration, golden, and failure-injection layers now exist;
  normal Python tests prohibit network access. Angular lint/unit/build,
  Playwright shell smoke, Docker Compose smoke, dependency scans, image scans,
  and main-only GitHub Actions jobs are implemented.
- Public-repository audit found no high-confidence secret in tracked content or
  reachable Git history; a full-history Gitleaks CI job now guards future
  pushes.
- CI now uses one sequential job so one Docker image build is reused for
  Compose smoke, Playwright, and Trivy instead of consuming separate free-tier
  runner allocations. It builds `app` once, then starts app and worker from the
  shared `varys:local` image. The worker remains alive until a shutdown signal.
- Phase 1 handover and initial state artifact are prepared for the fixture-only
  authentication increment.
- Iteration 1A adds users, revocable PostgreSQL-backed sessions, Argon2id
  password hashing, the `varys create-admin` maintenance command, and login,
  logout, and current-user API endpoints. Login sessions use opaque server-side
  token hashes, an HttpOnly/Secure/SameSite=Lax cookie, 12-hour idle expiry,
  seven-day absolute lifetime, session rotation, CSRF-protected logout, and
  disabled-user/expired-session rejection.
- Iteration 1B implements the worker-facing PostgreSQL run domain: locked
  states, row-locked queued-run claiming, a transaction advisory lock for the
  one-active-run race, five-minute leases, heartbeats, expired-lease recovery,
  ordered append-only events, checkpointed pause/cancel controls, and safe
  terminal transitions. Migration `0003_run_dispatch`, unit tests, PostgreSQL
  integration tests, and worker startup reconciliation/claim integration are
  present. A clean Compose PostgreSQL run passed all four integration tests.
- Iteration 1C adds fixture-only Nifty 500 universe, Capital Market bhavcopy,
  and index-report adapters behind the common discovery/download/classify/verify
  contract. It records verified fixture metadata without mutating bytes and
  creates one isolated, safe `/data/work/<run-id>/` directory per run.

## Not implemented

- Iterations 1D through 1I and all Phase 2 through Phase 7 work.
- Product workflows beyond the Phase 0 test baseline.

## Known failing tests

No known failing tests. GitHub Actions passed after the Compose smoke workflow
was given its required CI-only `VARYS_SESSION_SECRET`, including Compose smoke,
Playwright, dependency audits, and Trivy.

## Known limitations

- A login/session restart is required before Phase 0 if the user has not yet
  started a fresh session since Docker-group membership was added.
- `/home/shivam/.profile` contains a stale VS Code environment source at line
  29. It emits a warning for login shells but does not block project commands.

## Open risks

- Docker client access remains unavailable in the current Codex session because
  it has not inherited Docker-group membership. Phase 0 Docker validation is
  nevertheless complete through the successful main CI run.
- Host resources are suitable for bootstrap, but later image builds should be
  monitored on this 7.2 GiB RAM development machine.
- No unresolved cross-document contradiction is known after the 2026-08-15
  planning alignment audit. Phase 1 must surface any new ambiguity before it
  changes a versioned contract or dependency baseline.
- This Codex session cannot access the Docker daemon, but the user completed a
  clean host-terminal Compose run on 2026-08-15: migrations, all four
  PostgreSQL integration tests, app/worker health checks, and cleanup passed.

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

`0003_run_dispatch` (head). Users, authentication sessions, runs, and
append-only run events exist; all other product tables remain unimplemented.

## Current output schema versions

- CSV representation: `v1`
- Equity CSV: `v1`
- Index CSV: `v1`
- Universe CSV: `v1`
- Manifest: `v1`
- Preparation report: `v1`

## Current Docker/runtime topology

`docker/Dockerfile` builds the Angular bundle and Python runtime into one image
used by both `app` and `worker`. `compose.yaml` defines app, worker, internal
PostgreSQL, persistent data volumes, and an optional disabled-by-default
`cloudflared` profile. FastAPI serves the Angular bundle at `/`; `/api/` and
`/files/` remain reserved server routes. The app entrypoint applies migrations
through the validated database helper before starting FastAPI. No image,
service, volume, or network has been daemon-validated in this Codex session.
The image uses current pinned Bookworm Python/Node bases, Debian security
upgrades, and removes unneeded `setuptools` and `wheel` after dependency
installation so their vendored build-time metadata is absent from the runtime
image scanned by Trivy. The image scan retains its HIGH/CRITICAL gate; its
temporary `.trivyignore` expires on 2026-09-15 and suppresses only two stale
third-party-SBOM findings for packages absent from the final package inventory.

The locked target topology is documented: FastAPI app and dedicated worker share
one Python codebase and application image, PostgreSQL is the only dispatch
authority, and production adds only cloudflared. No broker, microservice split,
Nginx, or separate scheduler is part of V1.

## Git workflow

- Use `main` as the default working branch through the first V1 release.
- Create or switch to a temporary branch only when the owner explicitly
  requests one for a specific risk, experiment, or review boundary.
- Use small, coherent, verified commits as review and rollback checkpoints.
- Phase approval remains owner-controlled and is independent of Git branching.

## Current developer commands

`make bootstrap`, `make format`, `make lint`, `make typecheck`, `make test`,
`make test-unit`, `make test-golden`, `make test-failure-injection`,
`make test-e2e`, `make check`, `make build`, `make compose-up`,
`make compose-down`, and `make compose-smoke` are implemented.

`make test-integration` now runs PostgreSQL-only tests and requires
`VARYS_TEST_DATABASE_URL`; it skips when that environment variable is absent.

The frontend commands are `npm --prefix frontend ci`, `npm --prefix frontend run
lint`, `npm --prefix frontend run build`, `npm --prefix frontend test --
--watch=false`, and `npm --prefix frontend run test:e2e`.

## Decisions due before later phases

- Phase 0 must lock all contracts listed in plan section 8.1 before Phase 1.
- Phase 0 must lock the exact index/universe schemas and optional-value
  semantics from the minimum approved baselines in plan sections 9.4 and 9.5.
- Live NSE discovery details are due before Phase 2.
- Production backup transport and Cloudflare settings are due before Phase 6.

## Next allowed implementation work

Start Phase 1 Iteration 1D only. Review affected contract, schema, toolchain,
and dependency versions in every increment; update their versioned records
whenever a change is made.

## Build performance

The Dockerfile retains the pinned pip and npm dependency model. Its BuildKit
package-cache mounts preserve downloaded npm tarballs and Python wheels across
rebuilds without placing cache files in the final application image. The first
build still downloads base images and dependencies; subsequent builds reuse the
caches unless the Docker builder cache is pruned. The changed Dockerfile awaits
caches unless the Docker builder cache is pruned. GitHub Actions Compose smoke
passed with the changed Dockerfile; this Codex session still has no Docker
daemon access.
