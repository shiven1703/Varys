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

- Iteration 1A only: users, Argon2id password hashes, PostgreSQL-backed
  revocable sessions, `varys create-admin`, login/logout/current-user routes,
  secure session cookies, CSRF, expiry, and protected access.

## Out of scope

- Iterations 1B through 1I: runs, fixtures, parsing, package publication,
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

## Acceptance evidence

Phase 0 completed its required GitHub Actions CI suite and was explicitly
owner-approved on 2026-08-15. The owner accepted Iteration 1A on 2026-08-15.
Its local PostgreSQL and Compose evidence remains pending for the full Phase 1
acceptance suite.

## Version maintenance

Every Phase 1 increment must review affected dependency, toolchain, contract,
output-schema, parser, and API versions. Update lockfiles and the corresponding
versioned documents whenever a version changes; record the evidence in this
file and `docs/implementation/dependency-baseline.md`.

## Next actions

Start Iteration 1B only: run persistence, append-only events, PostgreSQL
claiming, leases, heartbeats, recovery, and safe pause/cancel controls. Do not
start a later Phase 1 iteration in the same increment.

## Owner approval

Phase 1 is not approved. Only the owner may approve it after the complete
Phase 1 acceptance suite passes.
