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

- Iteration 1I implementation, local acceptance, and owner acceptance complete;
  full GitHub Actions evidence pending.

## Out of scope

- Phase 2 and later work.

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

Iteration 1C adds the `SourceAdapter` protocol, all contract-required response
classifications, typed fixture references/responses/verification metadata, and
fixture-only implementations of `Nifty500UniverseSource`,
`CapitalMarketBhavcopySource`, and `IndexReportSource`. These classes import no
network, run-state, retry, parser, or publication code. `StoragePaths` now
creates an isolated canonical run workspace once; unit tests cover all three
adapters, valid/missing/empty fixture responses, verification metadata, and
workspace isolation.

Verified locally:

- `make format`
- `make check` — 30 unit tests passed; Ruff and mypy passed.
- `git diff --check`

The owner accepted Iteration 1C on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1D adds reviewed fixture parsers for legacy and UDiFF Capital Market
bhavcopies, Nifty index reports, and the Nifty 500 universe. Parser selection
for bhavcopies uses the actual, exact raw header; all raw schemas are guarded
and unknown or malformed inputs fail before canonical output. Only `EQ` rows
reach equity/universe output. The common canonical writer validates the locked
schema, Decimal/count/date types, required/optional cells, sorting, duplicate
business keys, UTF-8/LF encoding, and the literal-`NA` distinction. Golden
fixtures prove byte-identical equity, index, and universe output on repeated
runs.

Verified locally:

- `make format`
- `make check` — 34 unit tests passed; Ruff and mypy passed.
- `make test-golden` — 2 golden tests passed.
- `git diff --check`

The owner accepted Iteration 1D on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1E adds migration `0004_package_publication`, package/file metadata,
and a deterministic ZIP publication path. It generates manifest and
preparation-report members from validated metadata, writes exactly one
`.zip.part` staging file, reopens and verifies every ZIP member, atomically
renames only verified archives to the immutable ready root, and records ready
metadata only afterward in the caller's PostgreSQL transaction. Canonical CSV
members are rechecked for approved headers, row counts, and duplicate business
keys. Worker startup reconciles complete post-rename BUILDING archives and
quarantines missing, corrupt, or metadata-inconsistent ready records.

Verified locally:

- `make format`
- `make check` — 37 unit tests passed; Ruff and mypy passed.
- `make test-golden` — 2 golden tests passed.
- `make test-failure-injection` — 1 test passed.
- `make test-integration` — 5 PostgreSQL tests correctly skipped because
  `VARYS_TEST_DATABASE_URL` is not configured in this session, including the
  new publication/reconciliation test.
- `.venv/bin/alembic -c alembic.ini heads` — one head,
  `0004_package_publication`.
- `.venv/bin/alembic -c alembic.ini upgrade head --sql` — PostgreSQL migration
  SQL renders successfully without a live database.
- `git diff --check`

The owner accepted Iteration 1E on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1F adds injected-failure coverage around generated workspace CSV
writes, post-CSV verification, ZIP generation, the post-rename/pre-commit
boundary, post-commit archive integrity, and startup reconciliation. Failed
workspace writes leave only `.part` files; failed staging never becomes ready;
a replacement package identity can rebuild safely; a database rollback after
the final rename leaves the archive unavailable until reconciliation adopts it;
and a corrupt committed archive is quarantined.

Verified locally:

- `make format`
- `make check` — 37 unit tests passed; Ruff and mypy passed.
- `make test-golden` — 2 golden tests passed.
- `make test-failure-injection` — 3 tests passed.
- `make test-integration` — 6 PostgreSQL tests correctly skipped because
  `VARYS_TEST_DATABASE_URL` is not configured in this session, including the
  post-rename rollback, post-commit, and reconciliation failure matrix.
- `git diff --check`

The owner accepted Iteration 1F on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1G adds migration `0005_daily_run_trade_date`, which persists the
only accepted daily-run input and prevents duplicate nonterminal daily requests
for the same date. Authenticated JSON APIs now create/read daily runs, list
ordered events, and request valid controls. They expose package metadata without
filesystem paths. Authenticated downloads derive only from a package UUID and
verify ready state, server-side relative path, size, and SHA-256 before
streaming. Cookie-authenticated mutations require the server-side CSRF token;
the handlers only enqueue/control records and never execute worker work.

Verified locally:

- `make format`
- `make check` — 37 unit tests passed; Ruff and mypy passed.
- `make test-golden` — 2 golden tests passed.
- `make test-failure-injection` — 3 tests passed.
- `make test-integration` — 7 PostgreSQL tests correctly skipped because
  `VARYS_TEST_DATABASE_URL` is not configured in this session, including the
  new authenticated HTTP run/package/download workflow.
- `.venv/bin/alembic -c alembic.ini heads` — one head,
  `0005_daily_run_trade_date`.
- `.venv/bin/alembic -c alembic.ini upgrade head --sql` — PostgreSQL migration
  SQL renders successfully without a live database.
- `git diff --check`

The owner accepted Iteration 1G on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1H replaces the static Angular shell with a minimal authenticated
daily-run workspace. It uses the real cookie-authenticated APIs for login,
session recovery, daily-run creation, run/events/package refresh, and verified
ZIP download URLs. It stores only the CSRF token and selected opaque run ID in
browser session storage; all run, event, and package fields are reloaded from
the server after refresh. A non-ready package renders no download link, while a
ready-with-warnings package surfaces its warning state. The UI adds an
authenticated route guard and a responsive, minimal visual design without
mocked business data. `make demo-up` now builds and starts the local Compose
stack, waits for readiness, and invokes the existing interactive administrator
command without placing the password in configuration or shell history. The UI
automatically follows the browser's light or dark color preference, including
the authentication, operational, status, error, and download states.
Re-running `make demo-up` now detects and preserves an existing administrator
instead of prompting for a password or failing. Direct duplicate administrator
creation also reports a concise CLI validation error rather than a traceback.

Verified locally:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- `npm --prefix frontend test -- --watch=false` — 2 unit tests passed,
  including the incomplete-package download guard.
- `sh -n scripts/demo/up.sh` and `make --dry-run demo-up
  VARYS_ADMIN_USERNAME=operator`
- `make check` — 39 Python unit tests passed; Ruff and mypy passed.
- `git diff --check`

The owner accepted Iteration 1H on 2026-08-15. No Phase 1 acceptance status is
claimed.

Iteration 1I composes the accepted Phase 1 components into the fixture-only
daily workflow for `2026-08-14`. The worker now polls PostgreSQL, reconciles
and recovers dispatch state, claims one run transactionally, persists immutable
raw fixtures and canonical workspace CSVs, publishes a verified ready ZIP, and
finishes the run at a safe checkpoint. Both processes initialize the required
storage layout independently. Auth session writes complete in a serialized,
short transaction before run/package database work, preventing concurrent UI
refreshes from blocking the app event loop. The UI restores a fresh CSRF token
and polls nonterminal runs once per second until completion. Structured worker
errors include a redacted exception type/message and run ID.

The former shell-only Playwright test is replaced by the real browser slice. It
creates a runtime-random administrator without persisting credentials, logs in,
starts the fixture run, observes created/claimed/completed events, downloads the
ready ZIP, and verifies the archive plus the API checksum with the backend
inspector. Separate browser cases prove incomplete and unauthenticated package
downloads are blocked and logout revokes access. Compose smoke uses a separate
`varys_test` database with per-test cleanup so the real worker cannot consume
integration fixtures. Its controlled restart check leaves a run with an
expired claimed lease, restarts app/worker, and requires recovery through ready
publication.

Verified locally and in the owner Docker terminal:

- `make format` and `make check` — 42 unit tests passed; Ruff and mypy passed.
- `make test-golden` — 2 golden tests passed.
- `make test-failure-injection` — 3 failure-injection tests passed.
- `npm --prefix frontend run lint` and `npm --prefix frontend run build`.
- `npm --prefix frontend test -- --watch=false` — 3 frontend unit tests passed,
  including nonterminal polling and incomplete-package download guarding.
- `npm --prefix frontend run test:e2e` — 4 real-stack Playwright tests passed.
- `sh scripts/ci/restart-recovery.sh` — expired claimed run recovered and
  completed through a ready package after app/worker restart.
- `COMPOSE_PROJECT_NAME=varys-acceptance VARYS_RUN_E2E=1 make compose-smoke`
  — fresh image/database/storage, migration head `0005`, 7 PostgreSQL
  integration tests, restart recovery, 4 Playwright tests, and isolated volume
  cleanup passed.
- The owner-downloaded ZIP's three declared artifacts matched manifest sizes,
  row counts, and SHA-256 values; both market CSVs matched golden files byte for
  byte, and all raw provenance hashes matched the controlled fixtures.
- `.venv/bin/alembic -c alembic.ini heads` — one head,
  `0005_daily_run_trade_date`.
- `git diff --check`.

The owner accepted Iteration 1I on 2026-08-15. The full GitHub Actions run
remains required after this increment is committed; no Phase 1 acceptance
status is claimed yet.

## Acceptance evidence

Phase 0 completed its required GitHub Actions CI suite and was explicitly
owner-approved on 2026-08-15. Iterations 1A through 1I are owner-accepted.

Iteration 1B began after the owner accepted 1A. The owner accepted its initial
domain checkpoint on 2026-08-15. The scoped implementation now has its
migration, database constraints, tests, and worker integration. Its clean
Compose migration and PostgreSQL integration suite passed on 2026-08-15. It is
therefore owner-accepted on 2026-08-15.

The clean Iteration 1I Compose run now supplies live PostgreSQL evidence for
authentication, dispatch, migration head `0005`, publication/reconciliation,
authenticated APIs, restart recovery, and browser login-to-download. All local
Phase 1 acceptance layers pass, and the owner accepted Iteration 1I on
2026-08-15. Full GitHub Actions evidence for the Iteration 1I commit remains
outstanding.

## Version maintenance

Every Phase 1 increment must review affected dependency, toolchain, contract,
output-schema, parser, and API versions. Update lockfiles and the corresponding
versioned documents whenever a version changes; record the evidence in this
file and `docs/implementation/dependency-baseline.md`.

Iteration 1B changes no dependency, toolchain, API, output-schema, parser, or
contract version. It advances only the Alembic migration head to
`0003_run_dispatch`.

The post-1B Docker build optimization retains the exact pinned pip and npm
locks; BuildKit cache mounts are provided by the already-pinned Docker Buildx
toolchain. `make check` passed after the change, and GitHub Actions Compose
smoke passed with the changed Dockerfile.

Iteration 1C adds no dependency, toolchain, API, output-schema, parser, or
contract version; it implements the locked source-adapter and filesystem
contracts with fixture-only Python code.

Iteration 1D adds no dependency, toolchain, API, output-schema, parser-format,
or contract version. It implements the existing locked CSV and source-adapter
contracts with fixture-only parsers and writers.

Iteration 1E adds no dependency, toolchain, API, output-schema, parser-format,
or contract version. It advances only the Alembic migration head to
`0004_package_publication`.

Iteration 1F adds no dependency, toolchain, API, output-schema, parser-format,
contract, or migration version.

Iteration 1G adds no dependency, toolchain, output-schema, parser-format, or
contract version. Its APIs are additive within the locked `/api/v1` and
`/files` namespaces; it advances the Alembic head to `0005_daily_run_trade_date`.

Iteration 1H adds no dependency, toolchain, API, output-schema, parser-format,
contract, or migration version. It consumes the existing locked API surface.

Iteration 1I adds no dependency, toolchain, output-schema, parser-format,
contract, or migration version. The CSRF refresh endpoint is additive within
the locked `/api/v1` namespace. Existing pinned Python, Angular, Playwright,
Docker, PostgreSQL, and schema versions remain unchanged.

## Next actions

Commit owner-accepted Iteration 1I and run the full GitHub Actions suite. If CI
passes, set Phase 1 to `USER_APPROVAL_PENDING` and wait for explicit owner
approval. Do not start Phase 2 work in the same increment.

## Owner approval

Phase 1 is not approved. Only the owner may approve it after the complete
Phase 1 acceptance suite passes.
