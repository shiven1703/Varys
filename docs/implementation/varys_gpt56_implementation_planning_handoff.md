# Varys — GPT-5.6 Implementation-Planning Handoff

**Repository status note (2026-08-15):** This is an approved historical input
to the now-completed planning stage. Its requested planning deliverables were
materialized in `docs/implementation/implementation-plan.md`. Sections 11–13
describe the former planning task and must not be interpreted as a prohibition
on the now-authorized Phase 0 implementation. `main` is the default working
branch through the first V1 release; current execution follows the repository
implementation plan and phase state files.

## 1. Your role

Act as a senior full-stack architect and implementation planner for a solo developer.

You are planning a separate application named **Varys**. Varys acquires NSE/Nifty Indices market-data files, preserves immutable raw source files, prepares deterministic CSV packages, and lets the user download those packages for manual upload into the main Hodor application.

Do not restart product discovery. The major product, architecture, reliability, security, and operations gates are already locked.

Read the attached/source specification first:

```text
docs/implementation/varys_requirements_and_architecture_spec.md
```

Also respect the existing Hodor project documents, especially the principles that:

- Hodor owns business validation, Data Runs, corrections, publishing, and downstream use.
- Failed or partial data must never feed downstream processing.
- Raw data must remain immutable.
- Build thin real slices with expansion-friendly boundaries.
- Avoid enterprise/devops overkill.

## 2. Locked purpose

```text
NSE / Nifty Indices source reports
  -> Varys automated acquisition
  -> immutable raw source storage
  -> parsing and technical validation
  -> deterministic package generation
  -> authenticated user downloads package
  -> user manually uploads package into Hodor
```

Varys does not connect to Hodor's database and does not own Hodor's business workflow.

## 3. Locked stack

```text
Frontend: Angular
UI: PrimeNG
Dense operational tables: AG Grid Community
Backend API: FastAPI
Background processing: one dedicated Python worker
Database: PostgreSQL for operational state only
Run dispatch: PostgreSQL-backed claiming, leases, and heartbeats
Runtime: Docker Compose
Production services: app, worker, postgres, cloudflared
External access: Cloudflare Access + Cloudflare Tunnel
Authentication: Varys username/password + PostgreSQL server-side sessions
CI/CD: GitHub Actions + GHCR
E2E: Playwright
```

Explicitly excluded in V1:

- RabbitMQ
- Redis
- Celery
- Kubernetes
- microservices
- separate scheduler container
- separate Nginx container
- separate object-storage server
- external observability stack

## 4. Locked functional scope

Varys supports:

- current Nifty 500 universe snapshot
- approximately five years of historical daily equity data for current constituents
- daily incremental equity data
- Nifty 50 index data
- Nifty 500 index data
- historical backfill
- daily scheduled acquisition
- source diagnostics and repair
- immutable raw-file archive
- deterministic Hodor-facing packages
- package download
- basic users and login

Equity source:

```text
NSE Capital Market daily bhavcopy
```

Required parser support:

- legacy Capital Market bhavcopy
- UDiFF Capital Market final bhavcopy

Only `EQ` rows are included.

Excluded fields:

- VWAP
- deliverable quantity
- deliverable percentage

Canonical equity CSV:

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

CSV null value:

```text
NA
```

## 5. Locked package model

Daily package:

```text
varys-market-data-YYYY-MM-DD.zip
  equity_market_data.csv
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

Universe package only when composition changes:

```text
varys-universe-YYYY-MM-DD.zip
  universe.csv
  manifest.json
  preparation_report.csv
```

Historical package:

```text
varys-backfill-START-END.zip
  universe.csv
  equity_market_data_YYYY.csv
  ...
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

Ready packages are immutable. Regeneration creates a new package/version.

## 6. Locked reliability rules

- one active run total
- worker uses PostgreSQL leases and heartbeats
- checkpoint every verified source file
- checkpoint every completed trading date
- backfills are resumable
- source files are immutable and content-addressed by SHA-256
- verified raw source files are retained permanently
- backfill and universe packages are retained permanently
- daily-package retention is configurable
- incomplete files use `.part`
- work happens only in isolated run directories
- no file under `/data/work` is downloadable
- final ZIP is verified and atomically renamed on the same filesystem
- database status changes to `READY` only after immutable final archive exists
- downloads require `READY` or `READY_WITH_WARNINGS` plus checksum match
- startup reconciliation repairs or quarantines inconsistent states
- missing/corrupt ready package gets one automatic regeneration attempt, then quarantine/manual action
- failed or partial outputs must never become downloadable

## 7. Locked acquisition behavior

Source adapters:

```text
Nifty500UniverseSource
CapitalMarketBhavcopySource
IndexReportSource
SecurityWiseRepairSource
```

Locked defaults:

```text
network concurrency: 1
base delay: 4 seconds
random additional delay: 1-3 seconds
transient retries: 3
session refresh attempts per file: 2
backfill batch size: 100 downloads
```

Daily schedule:

```text
timezone: Asia/Kolkata
first attempt: 20:00 IST
retry interval: 30 minutes
cutoff: 23:30 IST
```

Trading dates use:

```text
official/imported NSE holiday calendar
+ weekend filtering
+ actual report availability
```

Response classification must include:

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

The application supports persistent sessions, cookie persistence, NSE session bootstrap, configurable browser-compatible request profiles, session refresh, pacing, cooldowns, circuit breakers, diagnostics, and manual repair controls.

Manual repair controls:

- upload replacement source file
- override URL for one date
- retry discovery
- invalidate cached source file
- select conflicting source version
- resume from failed date

Do not design proxy rotation, CAPTCHA solving, or other dedicated anti-blocking bypass mechanisms.

## 8. Locked UI

Top-level screens:

```text
Dashboard
Daily Data
Historical Backfill
Files and Packages
Runs and Diagnostics
Settings and Users
```

Use PrimeNG for general UI and AG Grid Community only for dense tables.

## 9. Locked authentication/security

- no public self-registration
- first admin created through `varys create-admin`
- additional users created through authenticated UI
- all authenticated users have same operator permissions in V1
- Argon2id password hashing
- server-side sessions in PostgreSQL
- cookie: HttpOnly, Secure, SameSite=Lax
- idle timeout: 12 hours
- absolute lifetime: 7 days
- CSRF protection
- session rotation after login
- login throttling
- disabled-user session revocation
- package downloads require authentication
- Cloudflare Access is mandatory in production
- Varys login is still required behind Cloudflare Access

## 10. Locked testing/operations

Required testing:

- pytest unit tests
- parser tests
- mocked downloader tests
- golden-file tests
- PostgreSQL integration tests
- filesystem/failure-injection tests
- Angular tests
- Playwright E2E tests
- Docker Compose smoke tests
- production smoke tests

Normal CI must never call NSE.

Production deployment requires manual approval.

Observability:

```text
structured JSON logs
health endpoints
operational status inside Varys UI
email alerts
```

No Prometheus/Grafana/Loki/OpenTelemetry in V1.

Backups:

- nightly PostgreSQL logical backup
- encrypted off-VPS backups
- backup raw files and ready packages
- quarterly restore verification

## 11. What you must produce next

Create an implementation-planning package, not implementation code.

Produce:

1. **Architecture module breakdown**
   - backend modules
   - worker modules
   - Angular feature areas
   - PostgreSQL responsibility boundaries
   - filesystem responsibility boundaries

2. **Repository structure**
   - concrete monorepo folders
   - build/test/config locations
   - shared backend/worker code organization

3. **Implementation phases**
   - outcome-based phases
   - clear dependencies
   - first usable milestone
   - private production-deployment milestone

4. **Detailed Phase 0 and Phase 1 plan only**
   - implementation outcomes
   - implementation tasks
   - acceptance criteria
   - test expectations
   - manual review points
   - AI suitability where useful

5. **High-level placeholders for later phases**
   - no exhaustive implementation decomposition
   - no detailed planning for every future phase

6. **Key technical contracts to lock before coding**
   - index CSV schema
   - universe CSV schema
   - manifest schema
   - preparation report schema
   - run-state/stage model
   - source-adapter contract
   - API contract boundaries
   - output numeric/newline rules

7. **Risk register**
   - NSE source instability
   - parser/schema changes
   - partial-file/state corruption
   - worker crash/recovery
   - storage growth
   - authentication/session mistakes
   - deployment/backup failure

8. **Definition of Done**
   - per task
   - per phase
   - release acceptance

## 12. Planning style constraints

- Keep the plan maintainable by one developer.
- Prefer simple production-grade patterns.
- Do not add infrastructure that is not justified.
- Do not replace PostgreSQL-backed runs with a broker unless a concrete blocking need is proven.
- Do not split the backend into microservices.
- Preserve the single-image app/worker model.
- Do not produce code yet.
- Do not redesign the locked product boundaries.
- Ask questions only when a missing detail blocks implementation planning.
- Otherwise make reasonable implementation-planning assumptions and state them.

## 13. Recommended first response in the next chat

Start by:

1. confirming the locked architecture in a compact summary
2. listing the remaining contract decisions that must be locked before coding
3. proposing the implementation phases
4. detailing Phase 0 only after the user approves the phase structure

Do not jump directly into coding.
