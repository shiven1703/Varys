# Phase 1 State

Status: IN_PROGRESS
Owner approved: no
Plan revision: 3
Prerequisite: Phase 0 approved by the owner on 2026-08-15.
Started from commit: `568fc9d`
Current commit: Resolve with `git rev-parse HEAD` before each evidence update

## Goal

Deliver the fixture-only login-to-download vertical slice defined in section 11
of `docs/implementation/implementation-plan.md`, starting with Iteration 1A.

## Scope

- Iteration 1B owner-accepted on 2026-08-15: run persistence, append-only
  events, PostgreSQL claiming, leases, heartbeats, recovery, and safe
  pause/cancel controls.

## Out of scope

- Iterations 1C through 1I: fixtures, parsing, package publication,
  downloads, UI, and Phase 1 E2E acceptance.

## Implementation evidence

Iteration 1A began from `568fc9d` on 2026-08-15. It adds migration
`0002_authentication`, `users` and `auth_sessions`, Argon2id through pinned
`argon2-cffi==25.1.0`, opaque server-side session/CSRF token hashes, the
`varys create-admin --username <username>` maintenance command, and the
`/api/v1/auth/login`, `/logout`, and `/current-user` endpoints. Login revokes
previous active sessions for the user and emits an HttpOnly, Secure,
SameSite=Lax session cookie. A configured database now requires a session
secret of at least 32 characters. Sessions have a 12-hour rolling idle timeout
and seven-day absolute expiry; logout requires the returned CSRF token and
revokes the server-side record.

Verified locally:

- `make format`
- `make check` — 23 unit tests passed, Ruff and mypy passed.
- `.venv/bin/varys --help` — the maintenance command is installed.
- `make test-integration` — correctly skipped two PostgreSQL tests because
  `VARYS_TEST_DATABASE_URL` is not configured in this session.
- `git diff --check`

The migration and integration proof require a clean PostgreSQL database; Docker
and the configured PostgreSQL integration environment are unavailable in this
Codex session. They remain required Phase 1 acceptance evidence. The owner
accepted Iteration 1A on 2026-08-15; no Phase 1 acceptance status is claimed.

Iteration 1B extends the accepted initial domain checkpoint with migration
`0003_run_dispatch`: database-validated run and requested-action states, a
partial unique index for one active run, run-event sequence checks, and a
PostgreSQL trigger that rejects event updates and deletes. The worker performs
startup expired-lease recovery and transactional claim. Claims serialize the
empty-active-run race with a PostgreSQL transaction advisory lock while queued
records are row-locked with `SKIP LOCKED`. Unit tests cover checkpointed
pause/cancel and heartbeat ownership/expiry; the PostgreSQL integration tests
cover concurrent-claim exclusion, active lease protection, recovery, ordered
events, and the append-only trigger.

Verified locally:

- `make format`
- `make check` — 25 unit tests passed; Ruff and mypy passed.
- `make test-integration` — all four PostgreSQL tests correctly skipped because
  `VARYS_TEST_DATABASE_URL` is not configured.
- `.venv/bin/alembic -c alembic.ini history` and `heads` — one head,
  `0003_run_dispatch`.
- `.venv/bin/alembic -c alembic.ini upgrade head --sql` — PostgreSQL migration
  SQL renders successfully without a live database.
- `git diff --check`
- Host-terminal `make compose-smoke` — a clean Compose database migrated to
  `0003_run_dispatch`; all four PostgreSQL integration tests and the app/worker
  health checks passed; the scripted cleanup removed containers and volumes.

The Compose smoke command now passes the app container's configured PostgreSQL
URL to `VARYS_TEST_DATABASE_URL`, so `make compose-smoke` runs the complete
PostgreSQL integration suite instead of skipping it. Docker remains unavailable
in this Codex session, but the host-terminal run above is successful evidence.

## Acceptance evidence

Phase 0 completed its required GitHub Actions CI suite and was explicitly
owner-approved on 2026-08-15. The owner accepted Iteration 1A on 2026-08-15.
Its local PostgreSQL and Compose evidence remains pending for the full Phase 1
acceptance suite.

Iteration 1B began after the owner accepted 1A. The owner accepted its initial
domain checkpoint on 2026-08-15. The scoped implementation now has its
migration, database constraints, tests, and worker integration. Its clean
Compose migration and PostgreSQL integration suite passed on 2026-08-15. It is
therefore owner-accepted on 2026-08-15.

## Version maintenance

Every Phase 1 increment must review affected dependency, toolchain, contract,
output-schema, parser, and API versions. Update lockfiles and the corresponding
versioned documents whenever a version changes; record the evidence in this
file and `docs/implementation/dependency-baseline.md`.

Iteration 1B changes no dependency, toolchain, API, output-schema, parser, or
contract version. It advances only the Alembic migration head to
`0003_run_dispatch`.

## Next actions

Start Iteration 1C only: fixture source adapters and isolated run workspaces.
Do not start a later Phase 1 iteration in the same increment.

## Owner approval

Phase 1 is not approved. Only the owner may approve it after the complete
Phase 1 acceptance suite passes.
