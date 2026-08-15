# Varys Pre-Implementation Engineering Handover

**Original planning snapshot:** 2026-07-11  
**Repository alignment revision:** 2026-08-15  
**State represented:** Product and architecture approved; Phase 0 and Phase 1
planned in detail; application implementation not started.

## 1. Purpose and current use

This document preserves the engineering decisions that existed before
implementation. It is a traceability input, not the live execution ledger.

Current execution authority is:

1. `AGENTS.md`
2. `docs/implementation/varys_requirements_and_architecture_spec.md`
3. approved versioned contracts under `docs/contracts/`
4. approved architecture documents and ADRs under `docs/architecture/`
5. `docs/implementation/current-state.md`
6. reproducible tests and CI evidence
7. `docs/implementation/implementation-plan.md`
8. the current phase state under `docs/implementation/phases/`
9. this handover for original-planning traceability

Do not infer implementation from this document. Verify code, migrations,
runtime behavior, tests, and phase evidence from the repository.

## 2. Product boundary

Varys is a separate upstream application that:

```text
NSE / Nifty Indices source reports
  -> validated acquisition
  -> immutable raw-source preservation
  -> parsing and technical validation
  -> deterministic package generation
  -> authenticated user download
  -> manual upload into Hodor
```

Varys owns source acquisition, raw preservation, parsing, canonical output,
package publication/download, operational runs, diagnostics, repair, backfill,
scheduling, local users/sessions, and production safety.

Varys does not own Hodor data runs, business validation, symbol resolution,
corrections, publishing, ranking, indicators, or trading decisions. V1 has no
automatic Hodor database or API integration.

## 3. Locked V1 scope

- India/NSE end-of-day data only.
- Current Nifty 500 constituent snapshot.
- Approximately five years of equity history for a selected current snapshot;
  no point-in-time constituent reconstruction.
- Daily incremental equity data.
- Nifty 50 and Nifty 500 index data.
- Equity source: Capital Market daily bhavcopy.
- Legacy and UDiFF Capital Market formats.
- Only `series = EQ`.
- VWAP and delivery fields excluded.
- Official index and constituent reports.
- Security-wise report limited to diagnostics and controlled repair.

## 4. Locked architecture

```text
Frontend: Angular standalone components
General UI: PrimeNG
Dense grids: AG Grid Community
Backend: FastAPI
Worker: dedicated Python process
Database: PostgreSQL operational state only
Migrations: Alembic
Run dispatch: PostgreSQL row locking, leases, and heartbeats
Concurrency: exactly one active run total
Runtime: Docker Compose
Production services: app, worker, postgres, cloudflared
Registry: GHCR
CI: GitHub Actions
Browser E2E: Playwright
```

The app and worker share one Python codebase and one image with different
startup commands. FastAPI serves the Angular production bundle.

Excluded unless explicitly reopened by the owner and an ADR:

- Redis, RabbitMQ, Celery, or Kafka
- Kubernetes or microservices
- separate scheduler or Nginx service
- separate object-storage service
- external Prometheus/Grafana/Loki/OpenTelemetry stack

## 5. Repository workflow

`main` is the default working branch through the first V1 release. Do not create
or switch to a temporary branch unless the owner explicitly requests it for a
specific risk, experiment, or review boundary.

Use small coherent checkpoint commits on `main` when Git permission is granted.
Do not push or rewrite history without explicit authorization. Phase state and
owner approval remain mandatory even without a merge boundary.

Repository state documents are the progress and phase-completion ledger.

## 6. Run and package model

Approved run states:

```text
QUEUED
RUNNING
WAITING_FOR_SOURCE
PAUSED
SOURCE_BLOCKED
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
CANCELLED
```

`WAITING_FOR_SOURCE`, `PAUSED`, and `SOURCE_BLOCKED` retain the one-active-run
slot unless a later approved contract explicitly refines this behavior.

Approved package states:

```text
BUILDING
VERIFYING
READY
READY_WITH_WARNINGS
FAILED
QUARANTINED
SUPERSEDED
```

A download is permitted only when the package is ready, the final relative path
resolves under approved storage, the file exists, size matches, and SHA-256
matches metadata.

## 7. Persistent file model

```text
/data/
  raw/sha256/
  work/<run-id>/
  packages/staging/
  packages/ready/daily/
  packages/ready/universe/
  packages/ready/backfill/
  quarantine/
  diagnostics/
```

- Raw files are immutable and content-addressed.
- Ready packages are immutable.
- Work and staging are temporary and never downloadable.
- Different bytes for the same logical source/date create an explicit conflict.
- Durable writes use `.part`, flush, `fsync`, verification, same-filesystem
  atomic rename, and destination-directory `fsync` where required.
- Database readiness is recorded only after the immutable final archive exists.
- Startup reconciliation handles crashes at filesystem/database boundaries.

## 8. Canonical output baseline

### 8.1 Equity CSV

```text
trade_date
exchange
symbol
series
isin
previous_close
open_price
high_price
low_price
last_price
close_price
total_traded_quantity
turnover
number_of_trades
source_report
source_format_version
```

### 8.2 Index CSV minimum

```text
trade_date
index_code
index_name
open
high
low
close
volume_or_shares_traded_if_available
turnover_if_available
source_report
source_format_version
```

Phase 0 locks exact optional-value semantics. Unavailable canonical values use
literal `NA`.

### 8.3 Universe CSV minimum

```text
universe_code
snapshot_date
exchange
symbol
series
isin
company_name
industry
```

### 8.4 Representation

- UTF-8 without BOM.
- Comma delimiter.
- LF newline and required final newline.
- Dates as `YYYY-MM-DD`.
- Nulls as literal `NA`.
- Deterministic columns and rows.
- Decimal-safe numeric serialization.
- No binary-float artifacts, scientific notation, or implicit rounding.
- Normalize negative zero and trailing zeros according to the Phase 0 contract.
- No generation timestamps in market-data rows.

### 8.5 Packages

Daily:

```text
varys-market-data-YYYY-MM-DD.zip
  equity_market_data.csv
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

Universe, only when the snapshot changes:

```text
varys-universe-YYYY-MM-DD.zip
  universe.csv
  manifest.json
  preparation_report.csv
```

Backfill:

```text
varys-backfill-START-END.zip
  universe.csv
  equity_market_data_YYYY.csv
  ...
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

## 9. HTTP and authentication baseline

```text
/             Angular frontend
/api/v1/*     authenticated JSON APIs
/files/*      authenticated binary package downloads
```

- Initial administrator through `varys create-admin`.
- Argon2id password hashing.
- PostgreSQL server-side sessions.
- No public registration.
- Same operator permission level for V1 users.
- Cookie flags: HttpOnly, Secure, SameSite=Lax.
- Idle timeout: 12 hours.
- Absolute lifetime: 7 days.
- Login rotation, logout revocation, password-reset revocation, disabled-user
  revocation, CSRF, generic auth errors, and throttling are required by V1.
- Cloudflare Access plus Tunnel and the internal Varys login are both mandatory
  in production.

## 10. Phase 0 detailed outcomes

Phase 0 creates foundations only; it does not implement the market-data product
flow.

### 0A — Contracts

Create versioned CSV, manifest, preparation-report, run/package state,
source-adapter, API, configuration, and filesystem contracts. Resolve exact
index/universe schemas, numeric formatting, identifiers, ordering, and newline
rules needed by Phase 1.

### 0B — Architecture

Document repository structure, module boundaries, runtime topology,
PostgreSQL-backed run dispatch, and recoverable package publication in ADRs.

### 0C — Tooling

Create Python dependency/tool configuration, repository hygiene files, stable
root developer commands, and a captured dependency baseline.

### 0D — API and worker bootstrap

Create independent FastAPI and worker startup, configuration loading,
structured redacting logs, request IDs, liveness, and process tests.

### 0E — PostgreSQL and Alembic

Create SQLAlchemy sessions, migrations, PostgreSQL integration harness, and
readiness checks for connectivity and migration compatibility. Do not create
speculative product tables.

### 0F — Filesystem safety

Create safe path resolution, hashing, durable `.part` writes, atomic rename,
directory sync, storage readiness, traversal rejection, and failure tests.

### 0G — Angular shell

Create the standalone Angular/PrimeNG shell, approved route placeholders, API
client foundation, and tests. Placeholders must not display fake operations.

### 0H — Image and Compose

Create one multi-stage app/worker image, PostgreSQL topology, optional disabled
local `cloudflared` profile, Angular serving through FastAPI, persistent storage,
and Compose smoke tests.

### 0I — Test and CI baseline

Create test layers, PostgreSQL integration, golden/failure locations, Angular
validation, Playwright skeleton, network prohibition, image/Compose jobs,
dependency scanning, and container-image scanning. Required GitHub Actions run
on pushes to `main`.

### 0J — Repository execution loop

Create `docs/ai/START_HERE.md`, `docs/ai/AGENT_WORKFLOW.md`, current-state,
risk register, Definition of Done, dependency baseline, and phase evidence.

### Phase 0 acceptance

From a clean checkout, build and start the stack, migrate a clean PostgreSQL
database, verify liveness/readiness and the Angular shell, run all foundational
tests/scans/smoke checks, audit architecture/dependency drift, update state, and
stop at `USER_APPROVAL_PENDING` for explicit owner approval.

## 11. Phase 1 detailed outcomes

Phase 1 proves a real fixture-based login-to-download vertical slice without
live NSE access.

### 1A — Authentication

Users and sessions, Argon2id, create-admin, login/logout/current-user, secure
cookies, CSRF, expiry, route/API protection, and revocation.

### 1B — Runs and worker ownership

Run/event persistence, append-only events, database-enforced one-active-run,
transactional claim, lease, heartbeat, safe controls, and recovery.

### 1C — Fixture adapters and workspaces

Fixture universe/equity/index adapters implement the common adapter contract in
isolated non-downloadable run workspaces. Adapters do not own retries, run
transitions, or publication.

### 1D — Parsers and canonical writers

Legacy and UDiFF equity parsers, index/universe parsers, schema guards, `EQ`
filtering, deterministic Decimal-safe writers, and byte-identical golden files.

### 1E — Package publication and failure matrix

Manifest/report generation, deterministic archive policy, verification,
atomic publication, immutable identity, metadata transaction, reconciliation,
and injected failures across every filesystem/database boundary.

### 1F — APIs and downloads

`POST /api/v1/runs/daily` accepts only `trade_date` and returns `202`. A
conflicting active run returns `409` with `RUN_ALREADY_EXISTS`. Provide run,
event, control, and package metadata APIs. Downloads use `/files/*`, require
authentication/readiness, and validate relative path, size, and SHA-256.

### 1G — Daily UI and real-stack E2E

Login, authenticated shell, date selection, start action, persisted status and
events, warnings/errors, ready-package display, safe download, refresh recovery,
and Playwright against real APIs and PostgreSQL fixture state.

### 1H — Phase acceptance

From a clean checkout, migrate, create admin, log in, run the fixture workflow,
prove claims/leases/recovery/determinism/publication safety, download and verify
the package, run the failure matrix and Playwright flow, audit drift, update
state/risks, and stop for explicit owner approval.

## 12. Later phase guardrails

- Phase 2: live source acquisition, response classification, pacing/retries,
  circuit breaker, immutable raw archive, conflicts, and diagnostics.
- Phase 3: trading calendar, scheduler, cutoff/waiting behavior,
  change-triggered universe packages, retention, dashboard, and alerts.
- Phase 4: frozen-universe resumable backfill, sequential acquisition,
  checkpoints, yearly fingerprints/chunks, and deterministic publication.
- Phase 5: controlled repair, replacement upload, URL override, rediscovery,
  invalidation, conflict selection, audit, and package supersession.
- Phase 6: private Cloudflare topology, immutable GHCR images, hardened Compose,
  backup/migrate/deploy/health/rollback, and encrypted off-host backups.
- Phase 7: user administration, throttling/security headers, complete failure
  matrix, low-disk/alert tests, restore drill, and V1 acceptance.

These are phase-level guardrails, not implementation-ready decompositions.
Expand each only after the prior phase is owner-approved and the repository is
audited.

## 13. Repository-native execution and evidence

For every meaningful increment:

1. Verify `main`, exact commit, and working-tree state.
2. Read current authority, phase state, contracts, ADRs, risks, and dependency
   baseline.
3. Report scope, files, tests, assumptions, risks, and exclusions.
4. Implement the smallest coherent approved increment.
5. Run deterministic validation and self-review the diff.
6. Update current-state and phase evidence when facts change.
7. Create a small checkpoint commit on `main` when authorized.

Preserve:

- phase/iteration
- checkpoint SHA
- files changed
- exact commands and results
- CI run links when pushed
- image identifier and migration revision when applicable
- architecture/security/migration review notes
- deviations, limitations, risks, and follow-ups

Phase completion requires clean-environment acceptance, required checks green,
architecture/dependency review, truthful state/risk updates, and explicit owner
approval. Tests passing never authorize `APPROVED`.

## 14. Required state after Phase 0

- All required contracts exist and agree with the specification.
- Architecture/module/runtime documents and ADRs exist.
- Root developer commands work from a clean checkout.
- API and worker boot independently from one Python codebase.
- PostgreSQL/Alembic and readiness checks work.
- Durable filesystem helpers and failure tests work.
- Angular shell builds and is served by FastAPI.
- App and worker share one image; Compose starts app/worker/postgres.
- Optional local `cloudflared` is disabled by default.
- Test layers and uncontrolled-network prohibition work.
- Dependency and image scans are configured.
- Repository workflow/state/risk/Definition-of-Done documents exist.
- Clean-environment acceptance and architecture drift review pass.
- Owner approval is recorded.

## 15. Required state after Phase 1

- Users and revocable PostgreSQL sessions work.
- Argon2id, create-admin, login/logout/current-user, CSRF, expiry, and route
  protection work.
- One active run is database-enforced.
- Append-only events, claims, leases, heartbeats, and recovery are proven.
- Fixture adapters use the approved contract and isolated workspaces.
- Legacy/UDiFF semantic parity and exact contracts are golden-tested.
- Manifest/report/archive publication is deterministic, verified, atomic, and
  immutable.
- Failure injection proves no partial or malformed package is downloadable.
- APIs and downloads match the approved routes/contracts.
- Angular and Playwright prove the real login-to-download fixture flow.
- Clean-checkout acceptance, drift review, state update, and owner approval are
  complete.

## 16. Known planning risks

- Official source URLs, responses, and schemas may change.
- Parser drift can silently corrupt output without strict guards/golden files.
- Filesystem/database publication boundaries require recovery testing.
- Worker crashes require leases, checkpoints, and idempotent recovery.
- Permanent raw retention and backfill require disk forecasting.
- Authentication/session mistakes can expose downloads or retain access.
- Deployment, backups, and restore procedures must be tested rather than
  assumed.
- Automated implementation can drift in scope without phase/state/ADR gates.

## 17. Final pre-implementation status

Planning is sufficiently detailed to start Phase 0. No application feature is
implemented by this document. Phase 0 must begin with exact contract lock,
proceed iteratively through foundations, pass clean-environment acceptance, and
stop for explicit owner approval before Phase 1.
