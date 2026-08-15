# Varys — Product Requirements and Architecture Specification

## 1. Purpose

Varys is a separate upstream application that acquires official NSE/Nifty Indices market-data files, preserves the original source artifacts, prepares deterministic CSV packages, and makes those packages available for manual upload into Hodor.

Varys is not part of the Hodor runtime and does not share Hodor's database, workflow state, or business logic.

The core flow is:

```text
NSE / Nifty Indices source reports
  -> Varys acquisition
  -> immutable raw-file preservation
  -> parsing and technical validation
  -> deterministic CSV/package generation
  -> authenticated user downloads package
  -> user manually uploads package to Hodor
  -> Hodor performs business validation, Data Run workflow, corrections, publishing, and downstream processing
```

## 2. Relationship to Hodor

Hodor remains the system of record for:

- Data Runs
- business validation
- symbol/instrument resolution
- manual corrections
- corporate-action review
- publish gating
- ranking and downstream calculations
- audit of business workflow

Varys is responsible only for reliable acquisition and preparation of import-ready files.

Varys must not:

- connect directly to Hodor's database
- publish data inside Hodor
- calculate rankings or indicators
- resolve Hodor business-validation issues
- manage Hodor Data Runs
- make buy/sell decisions
- become a general-purpose market-data analytics platform

## 3. Product Scope

### 3.1 Application identity

```text
Name: Varys
```

### 3.2 V1 datasets

Varys supports:

- current Nifty 500 constituent snapshot
- approximately five years of daily historical equity data for the current Nifty 500 constituents
- daily incremental equity data
- Nifty 50 index data
- Nifty 500 index data

Historical equity preparation uses the selected current Nifty 500 snapshot over historical prices. It is not point-in-time constituent reconstruction.

### 3.3 Market and frequency

```text
Market: India / NSE
Frequency: EOD only
Intraday: out of scope
Other countries/markets: out of scope for V1
```

### 3.4 User experience

Varys is a browser-first application with an Angular UI.

A CLI may exist only for maintenance, recovery, bootstrap, or debugging. It is not the normal operating interface.

### 3.5 Hodor transfer mechanism

V1 uses manual file transfer:

```text
Varys generates and exposes package
  -> user downloads package
  -> user manually uploads package into Hodor
```

No automatic Hodor API integration is required in V1.

## 4. Source Decisions

### 4.1 Universe source

Primary source:

```text
Official current Nifty 500 constituent CSV
```

The selected universe snapshot is preserved and versioned.

### 4.2 Equity source

Primary source:

```text
NSE Capital Market daily bhavcopy
```

Varys must support both:

- legacy Capital Market bhavcopy format
- UDiFF Capital Market final bhavcopy format

Parser selection must be based on actual columns/content, not filename alone.

### 4.3 Index source

Primary source:

```text
Official NSE / Nifty Indices daily and historical index reports
```

Required indices:

- NIFTY 50
- NIFTY 500

### 4.4 Security-wise report

The security-wise report is not the primary bulk source.

It may be used for:

- diagnostics
- targeted repair
- manual comparison
- missing-record investigation

### 4.5 Delivery data

Delivery quantity and delivery percentage are out of scope.

Varys does not download or merge delivery-position reports in V1.

### 4.6 Series scope

Only:

```text
series = EQ
```

is included in generated equity data.

## 5. Canonical Output Contracts

### 5.1 Equity CSV

Canonical columns:

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

VWAP is excluded.

Delivery fields are excluded.

### 5.2 Index CSV

The exact final column list must be locked during implementation planning, but it must include at least:

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

Only explicitly approved fields are exposed in generated canonical CSVs.

### 5.3 Universe CSV

The exact final column list must be locked during implementation planning, but it must include at least:

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

### 5.4 Raw-source preservation rule

Varys preserves the original downloaded source files unchanged.

All source fields remain available in immutable raw artifacts even when the canonical Hodor-facing CSV exposes only a selected stable schema.

Future NSE columns must not silently appear in Hodor-facing CSVs. A reviewed schema-version change is required.

### 5.5 CSV representation rules

Locked rules:

- encoding: UTF-8
- delimiter: comma
- deterministic column order
- deterministic row order
- date format: `YYYY-MM-DD`
- null representation: literal `NA`
- no generation timestamps inside market-data CSV rows
- provenance and timestamps belong in `manifest.json`

The exact newline convention and numeric formatting policy must be locked during implementation planning and covered by golden-file tests.

### 5.6 Daily package

```text
varys-market-data-YYYY-MM-DD.zip
  equity_market_data.csv
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

### 5.7 Universe package

Generated only when the Nifty 500 snapshot changes:

```text
varys-universe-YYYY-MM-DD.zip
  universe.csv
  manifest.json
  preparation_report.csv
```

### 5.8 Historical backfill package

```text
varys-backfill-START-END.zip
  universe.csv
  equity_market_data_YYYY.csv
  equity_market_data_YYYY.csv
  ...
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

The exact selected universe snapshot is included in the backfill package.

## 6. Completeness Rules

A package may become downloadable only when:

- required equity source report exists and passes verification
- required index source data exists and passes verification
- selected Nifty 500 universe snapshot exists
- only valid `EQ` rows are selected
- output CSV contracts pass validation
- row counts are recorded
- checksums are recorded
- manifest file references match the actual package files
- the final archive has been reopened and verified
- final publication completed atomically

A package with only non-blocking warnings may become:

```text
READY_WITH_WARNINGS
```

Blocking failures prevent publication.

## 7. Runtime Architecture

### 7.1 Technology choices

```text
Frontend: Angular
General UI: PrimeNG
Dense operational grids: AG Grid Community
Backend API: FastAPI
Background processing: dedicated Python worker
Database: PostgreSQL
Runtime: Docker Compose
External access: Cloudflare Tunnel + Cloudflare Access
Image registry: GitHub Container Registry
CI/CD: GitHub Actions
```

### 7.2 Production services

```text
app
worker
postgres
cloudflared
```

The `app` and `worker` services use the same Python codebase and Docker image, with different startup commands.

### 7.3 Angular hosting

The Angular production build is copied into the application image and served by FastAPI.

```text
/          Angular frontend
/api/*     FastAPI APIs
/files/*   authenticated file downloads
```

No separate Nginx container is required in V1.

### 7.4 Explicitly excluded infrastructure

V1 does not use:

- RabbitMQ
- Redis
- Celery
- Kafka
- Kubernetes
- microservices
- separate object-storage server
- separate scheduler container
- external observability stack

## 8. Background Worker and Run Model

### 8.1 Why the worker exists

Long-running downloads, backfills, parsing, validation, and package generation must never run inside request/response handling.

The API creates and controls runs. The dedicated worker claims and executes them.

### 8.2 PostgreSQL-backed run claiming

The worker uses PostgreSQL row locking, leases, and heartbeats.

A run contains at least:

```text
status
stage
worker_id
lease_expires_at
heartbeat_at
attempt_count
next_retry_at
current_trade_date
last_completed_trade_date
last_error
```

### 8.3 Run states

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

A low-disk pause may use a dedicated stage/reason such as `PAUSED_LOW_DISK`.

### 8.4 Reliability behavior

The worker must:

- claim work transactionally
- renew leases while active
- heartbeat periodically
- checkpoint after every verified source file
- checkpoint after every completed trading date
- reuse verified cached files
- resume from safe checkpoints
- recover expired leases
- stop pause/cancel operations only at safe checkpoints

### 8.5 Concurrency

V1 allows exactly one active run total.

This includes:

- daily runs
- historical backfills
- repair runs
- package regeneration

Additional runs remain queued.

### 8.6 Scheduler

The scheduler runs inside the worker process.

It must:

- schedule the daily run
- use PostgreSQL locking to prevent duplicate scheduling
- detect missed runs after restart
- create a run only if an equivalent one does not already exist

## 9. PostgreSQL Scope

PostgreSQL stores operational state only.

Required core tables/concepts:

```text
users
auth_sessions
runs
run_events
source_files
source_file_conflicts
universe_snapshots
generated_packages
generated_package_files
application_settings
audit_events
```

It does not store the full five-year OHLC dataset.

Use Alembic migrations, foreign keys, uniqueness constraints, and transactional state transitions.

## 10. Persistent Filesystem Design

### 10.1 Layout

```text
/data/
  raw/
    sha256/
  work/
    <run-id>/
  packages/
    staging/
    ready/
      daily/
      universe/
      backfill/
  quarantine/
  diagnostics/
```

### 10.2 Raw storage

Raw files are immutable and content-addressed by SHA-256.

Example:

```text
/data/raw/sha256/ab/abcdef...zip
```

Rules:

- raw files are never overwritten
- identical hashes reuse the same stored artifact
- different content for the same source/date creates a conflict
- conflicts require explicit review or selection
- original filenames are retained as metadata

### 10.3 Retention

Locked:

- verified raw NSE source files: retain permanently
- universe packages: retain permanently
- backfill packages: retain permanently
- daily packages: configurable retention
- work/staging files: temporary and excluded from backups

### 10.4 Isolated run workspace

Each run receives:

```text
/data/work/<run-id>/
```

Nothing under `/data/work` is downloadable.

### 10.5 Atomic file creation

CSV files are written as:

```text
filename.csv.part
```

The worker must:

1. write deterministically
2. flush buffers
3. call `fsync`
4. close
5. reopen
6. verify schema and column order
7. count rows
8. verify required values and uniqueness
9. calculate SHA-256
10. rename to the completed internal filename

No `.part` file can enter a downloadable package.

## 11. Transaction-Safe Package Publication

A filesystem operation and a database transaction cannot form one ACID transaction. Varys uses a recoverable two-phase publication protocol.

### 11.1 Package states

```text
BUILDING
VERIFYING
READY
READY_WITH_WARNINGS
FAILED
QUARANTINED
SUPERSEDED
```

### 11.2 Build phase

A PostgreSQL transaction creates a package record with `BUILDING` status.

The worker writes only inside its isolated work directory.

### 11.3 Verification phase

Before finalisation, verify:

- all required files exist
- no `.part` files remain
- schemas are recognised
- headers and column order are correct
- row counts match
- duplicate business keys are absent
- manifest filenames match package files
- manifest checksums match package files
- ZIP archive can be reopened
- every ZIP member can be read

### 11.4 Atomic filesystem publication

The final archive is built as:

```text
/data/packages/staging/<package-id>.zip.part
```

Then:

1. flush and `fsync`
2. close and reopen
3. verify archive and members
4. atomically rename on the same filesystem into `/data/packages/ready/...`
5. `fsync` the destination directory

### 11.5 Database readiness transaction

Only after the immutable final archive exists successfully, one PostgreSQL transaction:

- records final relative path
- records size and SHA-256
- records file metadata
- marks package `READY` or `READY_WITH_WARNINGS`
- marks run completed
- writes completion events

A package is downloadable only when:

```text
status is READY or READY_WITH_WARNINGS
AND final file exists
AND checksum matches database metadata
```

### 11.6 Crash recovery

- crash before final rename: package unavailable; rebuild or resume
- crash after rename but before DB commit: complete file remains unavailable until reconciliation adopts or quarantines it
- crash after DB commit: package remains valid and downloadable

### 11.7 Startup reconciliation

The worker checks:

- expired run leases
- `BUILDING` packages with complete ready files
- `READY` records with missing/corrupt files
- stale `.part` files
- abandoned work directories
- unreferenced raw artifacts
- checksum mismatches

Missing/corrupt ready-package policy:

```text
Attempt automatic regeneration once when all raw inputs exist.
If regeneration fails, quarantine and require manual action.
```

### 11.8 Ready-package immutability

Ready packages are never overwritten.

Regeneration creates a new package ID, version, checksum, and manifest.

## 12. Historical Backfill

### 12.1 Flow

```text
freeze universe snapshot
  -> build expected trading-date list
  -> skip verified cached files
  -> acquire missing equity reports sequentially
  -> acquire missing index reports sequentially
  -> checkpoint every verified file
  -> classify missing dates
  -> prepare yearly equity chunks
  -> retry unresolved dates
  -> finalise only after blocking gaps are resolved
```

### 12.2 Batch size

```text
100 network downloads per batch
```

Batch size affects checkpointing/reporting only. Concurrency remains one.

### 12.3 Yearly chunk checkpointing

Each yearly chunk has states:

```text
BUILDING
VERIFIED
FAILED
```

Verified chunks can be reused only when the dependency fingerprint matches:

- source-file checksums
- universe snapshot ID
- parser version
- output schema version
- configuration fingerprint

## 13. NSE Acquisition Automation

### 13.1 Source adapters

```text
Nifty500UniverseSource
CapitalMarketBhavcopySource
IndexReportSource
SecurityWiseRepairSource
```

Each adapter provides:

```text
discover(date)
download(reference)
classify(response)
verify(file)
```

Discovery/download logic must remain isolated from parsing and package generation.

### 13.2 Session behavior

Varys supports:

- persistent HTTP sessions
- cookie persistence
- NSE session bootstrap
- configurable browser-compatible request profiles
- standard redirects and compression
- connection reuse
- session refresh on ordinary expiration
- request/response diagnostics
- stable profile for each run

### 13.3 Request pacing

Locked defaults:

```text
concurrency: 1
base delay: 4 seconds
random additional delay: 1-3 seconds
transient retries: 3
maximum session refresh attempts per file: 2
```

All are configurable.

### 13.4 Response classification

```text
VALID_FILE
NOT_PUBLISHED_YET
KNOWN_NON_TRADING_DATE
NOT_FOUND
SESSION_EXPIRED
RATE_LIMITED
ACCESS_DENIED
CHALLENGE_RESPONSE
TRANSIENT_SERVER_ERROR
INVALID_CONTENT
CORRUPT_ARCHIVE
SCHEMA_CHANGED
```

HTTP 200 is not automatically success.

Varys rejects:

- HTML instead of expected ZIP/CSV
- challenge/denial responses
- zero-byte files
- truncated content
- malformed archives
- wrong trade dates
- unexpected schemas

### 13.5 Retry policy

```text
timeout / connection reset / 5xx
  -> exponential backoff
  -> maximum 3 retries

session expired
  -> refresh session
  -> retry same source file

not published yet
  -> wait configured interval
  -> retry later

429
  -> long cooldown
  -> resume later from checkpoint

403 or challenge response
  -> open source circuit
  -> stop automated acquisition
  -> preserve diagnostics
  -> require operator repair and controlled test
```

No infinite retry loops.

### 13.6 Source circuit breaker

Per source:

```text
CLOSED
OPEN
HALF_OPEN
```

The UI must show:

- source name
- failed URL
- classification
- HTTP status
- content type
- attempt count
- request profile
- sanitized response excerpt
- last successful request
- recommended operator action

A controlled test request is required before returning an open circuit to normal operation.

### 13.7 Manual repair controls

Authenticated users may:

- upload a replacement raw source file
- override source URL for one date
- retry source discovery
- invalidate an incorrect cached file
- select among conflicting source versions
- resume from the failed date

Manually supplied files must pass the same checksum, date, archive, schema, and parser validations as automated files.

## 14. Trading Calendar and Daily Scheduling

### 14.1 Trading-date source

Use:

```text
official/imported NSE holiday calendar
+ weekend filtering
+ actual report availability
```

An unexplained missing weekday remains a visible data issue and is not silently classified as a holiday.

### 14.2 Daily schedule

```text
timezone: Asia/Kolkata
first attempt: 20:00 IST
retry interval: 30 minutes
final cutoff: 23:30 IST
```

If required reports remain unavailable at cutoff:

```text
run status = WAITING_FOR_SOURCE
```

Varys must never substitute prior-day data.

## 15. UI Requirements

Use Angular standalone components.

Top-level screens:

### 15.1 Dashboard

Show:

- latest successful daily package
- current universe snapshot
- active/queued run
- backfill progress
- failed/paused/blocked runs
- source-circuit status
- next scheduled run
- storage usage and low-disk warning
- worker heartbeat
- last backup result

### 15.2 Daily Data

Support:

- choose trading date
- start acquisition
- inspect stage progress
- inspect source files
- view blocking errors and warnings
- retry/resume
- download ready package

### 15.3 Historical Backfill

Support:

- start/end date
- universe snapshot selection
- create backfill
- progress by date/year
- inspect missing/failed dates
- pause/resume/cancel
- retry failed dates
- download completed package

### 15.4 Files and Packages

Sections:

```text
Raw Source Files
Generated Packages
```

Show:

- source/report type
- trade date/range
- original filename
- size
- SHA-256
- validation state
- parser/schema version
- package readiness
- download action

### 15.5 Runs and Diagnostics

Show:

- run type and state
- stage and progress
- attempts
- latest error
- structured event history
- acquisition diagnostics
- source-circuit status
- valid controls for retry/pause/resume/cancel

### 15.6 Settings and Users

Settings:

- daily schedule
- request delay
- retry configuration
- backfill batch size
- request profile
- universe refresh interval
- package retention
- disk threshold
- output schema version
- alert email

Users:

- create user
- enable/disable user
- reset password
- view last login

## 16. Authentication and Authorization

### 16.1 User model

```text
id
username
password_hash
enabled
created_at
updated_at
last_login_at
```

### 16.2 Authorization

All authenticated users have the same operator permissions in V1.

No public registration, complex roles, organizations, or invitation workflows.

### 16.3 Password handling

- Argon2id hashing
- no plaintext storage/logging
- minimum password policy
- manual user creation
- no email reset flow
- authenticated operator may reset another user's password

### 16.4 Initial administrator

Created through a controlled maintenance command:

```text
varys create-admin
```

The password is read interactively or from a protected runtime secret.

### 16.5 Session design

Use server-side sessions stored in PostgreSQL.

Cookie flags:

```text
HttpOnly
Secure
SameSite=Lax
```

Session limits:

```text
idle timeout: 12 hours
absolute lifetime: 7 days
```

Required controls:

- session rotation after login
- immediate logout/revocation
- revocation after password reset
- disabled-user session revocation
- CSRF protection
- login-attempt throttling
- generic authentication errors
- authentication required for downloads

## 17. Secure Deployment

### 17.1 Access path

```text
Browser
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> Varys application
  -> Varys application login
```

Cloudflare Access is mandatory in production.

Both layers are required:

- Cloudflare Access at the perimeter
- Varys username/password login inside the application

### 17.2 Exposure rules

Do not publicly expose:

- FastAPI port
- PostgreSQL
- worker
- package filesystem
- Docker daemon

### 17.3 Security baseline

- containers run as non-root where practical
- secrets remain outside Git
- PostgreSQL uses internal Compose networking only
- downloads go through authenticated endpoints
- browser input never controls raw filesystem paths
- login and download endpoints are rate-limited
- security headers are applied
- server administration uses Tailscale/VPN/provider console
- public password-based SSH is not used

### 17.4 Audit events

Record:

- login/logout/failed login
- user create/enable/disable/password reset
- run create/pause/resume/cancel
- manual source upload
- source URL override
- cached-file invalidation
- conflict-version selection
- package generation/download
- settings changes
- source-circuit test/reset

Never record passwords, cookies, session tokens, or sensitive headers.

## 18. Testing Requirements

### 18.1 Backend and worker tests

Use `pytest`.

Required coverage:

- source discovery
- session bootstrap/refresh
- response classification
- retry/cooldown
- circuit breaker
- legacy parser
- UDiFF parser
- index parser
- universe parser
- EQ filtering
- schema validation
- `NA` handling
- manifest/checksum generation
- package finalisation
- run lease/heartbeat logic

### 18.2 Golden-file tests

Fixed fixtures must produce byte-identical output.

Golden tests lock:

- column order
- row order
- date formatting
- numeric formatting
- null representation
- newline convention
- manifest fields
- checksums

### 18.3 PostgreSQL integration tests

Test:

- one-run claim semantics
- duplicate-run prevention
- expired-lease recovery
- pause/resume
- safe cancellation
- transactional package state changes
- session revocation
- disabled-user access revocation

### 18.4 Filesystem and failure-injection tests

Inject failure:

- during download
- after raw rename/before DB metadata commit
- during CSV write
- after CSV verification
- during ZIP generation
- after atomic rename/before DB readiness commit
- after DB commit
- during low disk
- during regeneration

Every scenario must prove:

```text
No partial package is downloadable.
No READY package is malformed.
No READY package is overwritten.
Interrupted work can resume or safely rebuild.
```

### 18.5 Angular tests

Focus on:

- login/logout
- route guards
- run creation
- progress display
- pause/resume/retry/cancel
- blocked-source diagnostics
- package download authorization
- user management
- settings validation

### 18.6 Playwright E2E

Locked framework: Playwright.

Critical flows:

1. login and complete fixture-based daily run
2. start small backfill, simulate failure, resume
3. verify incomplete package cannot download
4. disable user and confirm access revocation
5. repair blocked source with replacement fixture and resume

Normal CI must not call NSE.

Manual deployed diagnostics may call NSE.

## 19. CI/CD

### 19.1 Repository checks

Owner-approved workflow amendment (2026-08-15): this solo-developer repository
uses `main` as the default working branch through the first V1 release. A
temporary branch is used only when the owner explicitly requests one for a
specific risk, experiment, or review boundary. The check suite below runs
locally and in GitHub Actions for pushes to `main`; this workflow amendment does
not weaken or remove any check.

```text
Python formatting/linting
Python type checks
pytest
Golden-file tests
PostgreSQL integration tests
Angular lint/tests
Angular production build
Playwright E2E
Docker image build
Dependency scan
Container image scan
Docker Compose smoke test
```

Required checks must pass before phase acceptance and before a production image
is eligible for deployment.

### 19.2 Main branch build

- build one immutable application image
- tag with Git SHA and release version
- push to GHCR
- use same image for app and worker
- retain previous deployable versions

### 19.3 Production deployment

Manual approval is required.

Sequence:

```text
approve deployment
  -> PostgreSQL backup
  -> disk-space check
  -> pull versioned image
  -> run Alembic migrations
  -> restart app and worker
  -> health checks
  -> smoke tests
```

No Kubernetes, staging environment, or blue-green deployment in V1.

## 20. Health, Observability, and Alerts

### 20.1 Health endpoints

```text
/api/health/live
/api/health/ready
```

Readiness checks:

- PostgreSQL connectivity
- migration compatibility
- required storage paths
- filesystem write capability

NSE availability does not make the application unhealthy.

### 20.2 Worker health

Track:

- last heartbeat
- scheduler heartbeat
- active run
- current stage
- lease expiry
- latest successful daily run

### 20.3 Logging

Use structured JSON logs with:

```text
timestamp
level
service
request_id
run_id
user_id
source_type
trade_date
event
error_code
safe_details
```

Never log secrets, passwords, cookies, or tokens.

### 20.4 Lightweight observability

V1 uses:

- structured logs
- health endpoints
- operational metrics in the Varys UI
- email alerts

No Prometheus, Grafana, Loki, or OpenTelemetry in V1.

### 20.5 Alerts

Alert on:

- daily run not completed by cutoff
- source circuit opened
- missing worker heartbeat
- repeated run failure
- low disk
- backup failure
- package reconciliation failure

## 21. Backup and Restore

### 21.1 Backups

- nightly PostgreSQL logical backup
- encrypted backup outside the VPS
- backup immutable raw source files
- backup ready universe packages
- backup ready backfill packages
- back up daily packages according to retention policy

Do not back up:

```text
/data/work
/data/packages/staging
```

### 21.2 Restore verification

Locked frequency:

```text
Quarterly
```

Verify:

- PostgreSQL restore into temporary database
- backup readability
- selected raw-file checksums
- at least one ready package opens and validates

## 22. Release Acceptance Criteria

A release is production-ready only when:

- all required CI checks pass
- database migrations succeed
- app and worker health checks pass
- application login works
- unauthorized access is blocked
- fixture-based daily generation succeeds
- package checksum validation succeeds
- incomplete package download is rejected
- previous image version remains available
- latest backup state is healthy

## 23. Locked Decision Summary

```text
Application name: Varys
Frontend: Angular
Backend: FastAPI
Background processing: dedicated Python worker
Database: PostgreSQL metadata/workflow only
Queue: PostgreSQL-backed claiming with leases/heartbeats
Concurrency: one active run total
Runtime: Docker Compose
Services: app, worker, postgres, cloudflared
External access: Cloudflare Access + Tunnel
Application authentication: local username/password + server sessions
Package transfer to Hodor: manual download/upload
Raw files: immutable, content-addressed, retained permanently
Ready packages: immutable
Daily-package retention: configurable
Backfill/universe retention: permanent
CSV null representation: NA
Equity series: EQ only
VWAP: excluded
Delivery fields: excluded
Normal CI live NSE calls: forbidden
Playwright: required
Production deployment approval: manual
External observability stack: excluded in V1
Restore verification: quarterly
```

## 24. Remaining Details for Implementation Planning

The next planning stage must still decide:

- exact index CSV schema
- exact universe CSV schema
- exact numeric formatting and rounding rules
- exact newline convention
- canonical parser/source-format identifiers
- exact PostgreSQL schema and indexes
- exact run stage model
- exact API endpoints and request/response contracts
- exact Angular route/component structure
- exact source URL-discovery approach
- exact backfill start/end-date defaults
- exact disk-space estimation formula
- exact backup transport/tool
- exact email provider/configuration
- exact dependency/version baseline
- phase/iteration breakdown and implementation order

These are implementation-planning decisions, not reasons to reopen the locked gates above.
