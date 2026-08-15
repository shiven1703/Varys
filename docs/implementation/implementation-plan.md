# Varys — GPT-5.6 Sol / Codex Implementation Plan

**Document purpose:** Primary implementation playbook for building Varys with OpenAI Codex using GPT-5.6 Sol.  
**Planning state:** Baseline plan; implementation phases are intentionally iterative.  
**Plan revision:** 3 — repository-native progress and main-first V1 workflow aligned 2026-08-15.  
**Human authority:** A phase is never considered approved or complete until the project owner explicitly says so.  
**Working model:** Each implementation phase starts in a new Codex chat/session. State is carried forward through repository documentation and reproducible tests, not conversational memory.

---

## 1. Purpose of this plan

This document converts the approved Varys product and architecture specification plus the pre-implementation Phase 0/Phase 1 planning into a repository-driven implementation workflow for Codex.

The intended loop is:

```text
approved architecture
  -> repository implementation plan
  -> one implementation phase in one Codex chat
  -> iterative code/test/review cycles
  -> phase acceptance tests
  -> USER_APPROVAL_PENDING
  -> explicit owner approval
  -> next phase starts in a fresh chat
```

The plan deliberately separates:

- **engineering evidence** from conversational claims,
- **acceptance-test success** from human approval,
- **phase readiness** from phase completion,
- **planning documents** from generated application state.

Codex must never infer that a phase is complete merely because all tests pass.

---

## 2. Source baseline and authority order

The original planning inputs are:

1. `docs/implementation/varys_requirements_and_architecture_spec.md`
2. `docs/implementation/varys_gpt56_implementation_planning_handoff.md`
3. `docs/implementation/varys_llm_handover_pre_implementation.md`

Only the engineering decomposition relevant to implementation is retained.

When implementation sources disagree, use this authority order:

1. Approved Varys product and architecture specification.
2. Approved versioned contracts under `docs/contracts/`.
3. Approved ADRs and architecture documents under `docs/architecture/`.
4. `docs/implementation/current-state.md`.
5. Reproducible tests and CI evidence.
6. This implementation plan.
7. The two historical planning handoffs, for traceability only.
8. Conversational statements from an earlier Codex chat.

A later approved contract or ADR may refine this plan. It must not silently contradict the locked architecture.

The planning handoffs do not independently override this authority chain. Their
historical "planning only" workflow directions are superseded by this
repository plan and recorded owner decisions. Their locked engineering outcomes
remain inputs that must be traced into contracts, implementation, and acceptance
evidence.

---

## 3. Locked product boundary

Varys is an upstream market-data preparation application.

```text
NSE / Nifty Indices source reports
  -> Varys acquisition
  -> immutable raw-source preservation
  -> parsing and technical validation
  -> deterministic CSV/package generation
  -> authenticated user downloads package
  -> user manually uploads package into Hodor
```

Varys owns:

- official NSE/Nifty Indices source acquisition,
- raw-source preservation,
- source validation/classification,
- parsing,
- deterministic canonical output,
- package generation and verification,
- package download,
- operational run state,
- diagnostics,
- repair/backfill workflows,
- Varys users and sessions,
- production scheduling and operational safety.

Varys does **not** own:

- Hodor Data Runs,
- Hodor business validation,
- Hodor symbol/instrument resolution,
- Hodor corrections,
- Hodor publishing,
- Hodor ranking/indicator logic,
- buy/sell decisions,
- automatic Hodor database/API integration in V1.

---

## 4. Locked V1 architecture

Do not casually redesign these choices during implementation.

```text
Frontend: Angular standalone components
General UI: PrimeNG
Dense grids: AG Grid Community

Backend API: FastAPI
Worker: dedicated Python process
Database: PostgreSQL for operational state only
Migrations: Alembic

Run dispatch: PostgreSQL row locking + leases + heartbeats
Concurrency: exactly one active run total

Runtime: Docker Compose
Production services:
  - app
  - worker
  - postgres
  - cloudflared

Application image:
  - one Python/application image
  - app and worker use the same image
  - separate startup commands
  - Angular production bundle served by FastAPI

Production access:
  Browser
    -> Cloudflare Access
    -> Cloudflare Tunnel
    -> Varys application
    -> Varys local login

Registry: GitHub Container Registry
CI/CD: GitHub Actions
Browser E2E: Playwright
```

Explicitly excluded in V1 unless the owner reopens the architecture decision:

- Redis
- RabbitMQ
- Celery
- Kafka
- Kubernetes
- microservices
- separate scheduler container
- separate Nginx container
- separate object-storage service
- Prometheus/Grafana/Loki/OpenTelemetry stack

---

# PRE-PHASE — Ubuntu, Codex, Git, and local development bootstrap

This is the first implementation step. Do it before Phase 0.

## P.1 Goal

Create a predictable Ubuntu development host where Codex can:

- inspect and modify the repository,
- run Docker builds and Docker Compose,
- execute project validation commands,
- use Git safely,
- preserve a clean separation between host tooling and application runtime dependencies.

The project should prefer containers for application runtime dependencies. Do **not** install PostgreSQL, Angular CLI, application Python packages, or cloudflared globally on the Ubuntu host unless a later proven requirement justifies it.

## P.2 Recommended Ubuntu baseline

Prefer a supported Ubuntu LTS release. If provisioning a new development machine, Ubuntu 24.04 LTS is the preferred baseline.

Before changing the machine, record:

```bash
cat /etc/os-release
uname -a
uname -m
df -h
free -h
```

Store any machine-specific caveats outside the repository if they contain private host information.

## P.3 Required OS-level packages

Install a small host-tool baseline:

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  jq \
  unzip \
  make \
  openssh-client \
  ripgrep
```

Optional but useful:

```bash
sudo apt install -y tree shellcheck
```

Do not install these at the OS level for Varys unless Phase 0 proves they are needed:

```text
postgresql
redis-server
rabbitmq-server
nginx
nodejs
npm
python application dependencies
angular-cli
cloudflared
```

Reason: the application is intended to run reproducibly through Docker Compose, and the Codex CLI has a standalone Linux installer.

## P.4 Install Docker Engine and Docker Compose plugin

Use Docker's official Ubuntu repository rather than Ubuntu's older `docker.io` package if starting from a clean host.

The expected Docker components are:

```text
docker-ce
docker-ce-cli
containerd.io
docker-buildx-plugin
docker-compose-plugin
```

Follow the current official Docker Ubuntu installation procedure, then verify:

```bash
docker --version
docker buildx version
docker compose version
sudo docker run --rm hello-world
```

### Docker group decision

For convenience on a personal development machine, you may add your user to the `docker` group:

```bash
sudo usermod -aG docker "$USER"
```

Then log out and back in.

Security note: membership in the Docker group is effectively privileged host access. Do this only on a machine where that tradeoff is acceptable.

If you do not want that privilege, keep using `sudo docker ...`.

## P.5 Install Codex CLI

Use the official standalone installer on Linux:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Verify:

```bash
codex --version
```

Start Codex from the repository root:

```bash
codex
```

Sign in with the intended ChatGPT/OpenAI account when prompted.

The preferred project model is:

```text
GPT-5.6 Sol
```

Codex currently supports selecting the model and reasoning level from the CLI. For project configuration, use the GPT-5.6 alias when appropriate; it resolves to GPT-5.6 Sol.

## P.6 Recommended Codex project configuration

Create repository-scoped Codex configuration only after the project is trusted.

Suggested `.codex/config.toml` baseline:

```toml
model = "gpt-5.6"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

Rationale:

- GPT-5.6 is the alias for GPT-5.6 Sol.
- `high` is a strong default for architecture-sensitive implementation.
- `on-request` keeps privileged actions visible.
- `workspace-write` allows normal repository edits without giving unrestricted host access.

Do not set `danger-full-access` as a project default.

For unusually difficult architecture/reliability work, the human may temporarily select a higher reasoning level with `/model`.

## P.7 Git configuration

Verify Git identity before the first commit:

```bash
git --version
git config --global user.name
git config --global user.email
```

Set them if missing:

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL"
```

Recommended:

```bash
git config --global init.defaultBranch main
git config --global pull.ff only
```

GitHub CLI is optional. It is useful for authentication, PRs, and CI inspection, but it is not required to begin Phase 0.

## P.8 Host-level tools that should remain optional

The following may be added later if they have a concrete purpose:

- GitHub CLI (`gh`)
- VS Code or another editor
- `age`/`restic`/backup tooling for production backup work
- database client utilities for diagnostics
- Cloudflare tooling for production deployment
- vulnerability scanners used outside CI

Do not preload production infrastructure during Pre-Phase.

## P.9 Pre-Phase repository files

Before Phase 0 implementation begins, ensure the repository contains or is ready to contain:

```text
AGENTS.md
.codex/
  config.toml
docs/
  implementation/
    implementation-plan.md
    current-state.md
```

This document should be stored as:

```text
docs/implementation/implementation-plan.md
```

If the repository does not yet exist, initialize it and commit only the planning/bootstrap baseline first.

## P.10 Pre-Phase acceptance tests

All must pass:

```bash
git --version
curl --version
jq --version
rg --version
docker --version
docker buildx version
docker compose version
codex --version
docker run --rm hello-world
```

Repository checks:

- Git repository opens cleanly.
- `git status` is understood and intentional.
- `AGENTS.md` exists.
- `.codex/config.toml` exists or its absence is explicitly documented.
- This implementation plan exists under `docs/implementation/`.
- `docs/implementation/current-state.md` exists with truthful initial state.
- Codex starts from the repository root and can read the plan.
- Codex can create and remove a harmless test file within the workspace sandbox.
- Codex cannot silently make the phase `APPROVED`.

### Pre-Phase completion rule

Codex may record:

```text
PRE_PHASE_ACCEPTANCE = PASSED
PRE_PHASE_STATUS = USER_APPROVAL_PENDING
```

Only the owner may change the final status to:

```text
PRE_PHASE_STATUS = APPROVED
```

Phase 0 must not be treated as authorized until that approval is explicit.

---

# 5. Codex operating contract for the entire project

## 5.1 One phase = one new Codex chat

Every implementation phase begins in a fresh Codex chat/session.

The new chat must reconstruct state from the repository.

Codex must never rely on remembered conversational context from a prior phase.

## 5.2 Required reading at the start of every phase

Before editing code, Codex must read in this order:

1. `AGENTS.md`
2. `docs/implementation/implementation-plan.md`
3. `docs/implementation/varys_requirements_and_architecture_spec.md`
4. `docs/implementation/varys_gpt56_implementation_planning_handoff.md`
5. `docs/implementation/varys_llm_handover_pre_implementation.md`
6. `docs/implementation/current-state.md`
7. the current phase state file
8. relevant contracts under `docs/contracts/`
9. relevant ADRs under `docs/architecture/decisions/`
10. `docs/implementation/risk-register.md` if present
11. `docs/implementation/dependency-baseline.md` if present
12. `docs/implementation/definition-of-done.md` if present

Then it must inspect:

```bash
git status
git branch --show-current
git log -n 10 --oneline
```

It must run the smallest appropriate baseline validation before changing files.

## 5.3 Mandatory first response from Codex in each phase chat

Codex should report:

```text
Verified repository baseline
Current branch / commit
Current phase status
Scope it believes is approved
Relevant contracts/ADRs
Tests it will use
Known risks/blockers
Files/modules it expects to touch
Anything it will explicitly not change
```

If repository evidence contradicts this plan, Codex must stop and surface the contradiction instead of silently choosing one.

## 5.4 Phase state lifecycle

Use only these phase states:

```text
NOT_STARTED
IN_PROGRESS
BLOCKED
ACCEPTANCE_PENDING
USER_APPROVAL_PENDING
APPROVED
```

Allowed Codex transitions:

```text
NOT_STARTED -> IN_PROGRESS
IN_PROGRESS -> BLOCKED
BLOCKED -> IN_PROGRESS
IN_PROGRESS -> ACCEPTANCE_PENDING
ACCEPTANCE_PENDING -> IN_PROGRESS          # acceptance failed
ACCEPTANCE_PENDING -> USER_APPROVAL_PENDING
```

Forbidden Codex transition:

```text
USER_APPROVAL_PENDING -> APPROVED
```

Only the owner may authorize `APPROVED`.

If the owner asks for more changes while a phase is `USER_APPROVAL_PENDING`, return it to `IN_PROGRESS`.

## 5.5 Phase state files

Create:

```text
docs/implementation/phases/
  pre-phase.md
  phase-0.md
  phase-1.md
  phase-2.md
  phase-3.md
  phase-4.md
  phase-5.md
  phase-6.md
  phase-7.md
```

Minimum phase-state template:

```markdown
# Phase N State

Status: NOT_STARTED
Owner approved: no
Plan revision: 1
Started from commit: <sha-or-N/A>
Current commit: <sha-or-N/A>

## Objective

## Scope

## Out of scope

## Implementation iterations
- Iteration 1:
- Iteration 2:

## Acceptance criteria

## Acceptance evidence
- Command:
- Result:
- Evidence/artifact:

## Deviations from plan

## Known limitations

## Risks opened/closed

## Decisions/ADRs created

## Next actions

## Owner approval
Not approved.
```

Codex may update everything except claiming owner approval.

## 5.6 Current-state ledger

`docs/implementation/current-state.md` is the cross-phase handoff.

It must always state facts, not intentions.

Minimum sections:

```text
Repository commit
Approved phases
Current phase and status
Implemented capabilities
Not implemented
Known failing tests
Known limitations
Open risks
Current database migration revision
Current output schema versions
Current Docker/runtime topology
Current developer commands
Next allowed implementation work
```

## 5.7 Commit and branch strategy

Owner-selected solo-developer workflow: use `main` as the default working
branch through the first V1 release.

Create or switch to a temporary branch only when the owner explicitly requests
one for a specific risk, experiment, or review boundary. Keep commits small,
coherent, and verified so the owner can review or revert them independently.
Phase acceptance and owner approval remain mandatory state transitions
regardless of branch choice.

Before risky edits, create a Git checkpoint.

## 5.8 Codex implementation rules

Codex must:

- plan before editing,
- make the smallest coherent implementation increment,
- run relevant tests after each meaningful increment,
- self-review the diff,
- preserve architecture boundaries,
- document deviations,
- update state docs as code changes,
- keep tests deterministic,
- never use live NSE in normal CI,
- never weaken tests just to get green CI,
- never silently add a new infrastructure dependency,
- never expose raw filesystem paths to browser-controlled input,
- never mark a phase approved.

Codex must stop and surface the issue when:

- a requested change contradicts a locked architecture decision,
- a migration could destroy existing data and no approved migration path exists,
- a source schema change cannot be safely mapped,
- security requirements conflict,
- a test failure suggests corruption or nondeterminism,
- credentials or secrets are found in tracked files.

---

# 6. Repository structure target

Phase 0 should converge toward a concrete monorepo similar to:

```text
varys/
  AGENTS.md
  .codex/
    config.toml

  README.md
  Makefile
  pyproject.toml
  uv.lock
  package.json                  # only if root JS orchestration is justified
  .editorconfig
  .gitignore
  .gitattributes
  .env.example

  docker/
    Dockerfile
    entrypoints/
      app.sh
      worker.sh

  compose.yaml

  backend/
    varys/
      __init__.py
      api/
      auth/
      config/
      db/
      domain/
      health/
      logging/
      packages/
      runs/
      sources/
      storage/
      worker/
    tests/
      unit/
      integration/
      golden/
      failure_injection/
      fixtures/

  frontend/
    package.json
    angular.json
    src/
      app/
        core/
        shared/
        features/
          dashboard/
          daily-data/
          historical-backfill/
          files-packages/
          runs-diagnostics/
          settings-users/
    e2e/

  migrations/
    env.py
    versions/

  docs/
    ai/
      START_HERE.md
      AGENT_WORKFLOW.md

    architecture/
      repository-structure.md
      module-boundaries.md
      runtime-topology.md
      decisions/

    contracts/
      csv-representation-v1.md
      equity-csv-v1.md
      index-csv-v1.md
      universe-csv-v1.md
      manifest-v1.md
      preparation-report-v1.md
      run-state-model-v1.md
      package-state-model-v1.md
      source-adapter-v1.md
      api-conventions-v1.md
      configuration-v1.md
      filesystem-layout-v1.md

    implementation/
      implementation-plan.md
      current-state.md
      dependency-baseline.md
      definition-of-done.md
      risk-register.md
      phases/

  scripts/
    dev/
    ci/
    maintenance/

  .github/
    workflows/
```

Exact names may be refined in Phase 0. The important boundary is one repository and one Python application codebase shared by the API and worker.

---

# 7. Module responsibility boundaries

## 7.1 Backend/API

The FastAPI process owns:

- authentication/session HTTP endpoints,
- run creation/control endpoints,
- run/package/source read APIs,
- package download authorization,
- health endpoints,
- serving the Angular production bundle.

It does **not** perform long-running acquisition, parsing, backfill, or package generation inside request handlers.

## 7.2 Worker

The worker owns:

- run claiming,
- leases/heartbeats,
- scheduler,
- acquisition orchestration,
- parsing orchestration,
- package generation,
- checkpoints,
- pause/cancel safe points,
- reconciliation,
- recovery/regeneration.

## 7.3 Shared domain code

Shared Python modules own:

- domain types,
- contracts,
- database models/repositories,
- storage helpers,
- parser interfaces,
- source-adapter interfaces,
- canonical writers,
- package verification,
- configuration.

The API and worker must not duplicate business rules.

## 7.4 PostgreSQL

PostgreSQL stores operational state only.

Expected concepts:

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

Do not store the full five-year OHLC market-data dataset in PostgreSQL.

## 7.5 Filesystem

Persistent data layout:

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

Raw files and ready packages are immutable.

Work and staging are temporary and never downloadable.

---

# 8. Technical contracts that must be versioned

## 8.1 Required before Phase 1 implementation

Phase 0 must lock and version:

1. CSV representation rules.
2. Equity CSV schema.
3. Index CSV schema.
4. Universe CSV schema.
5. Manifest schema.
6. Preparation-report schema.
7. Run state model.
8. Package state model.
9. Source-adapter interface.
10. API conventions.
11. Configuration conventions.
12. Filesystem layout/path rules.
13. Canonical parser/source-format identifiers.
14. Numeric formatting and rounding policy.
15. Newline convention.
16. deterministic row ordering.

## 8.2 Decisions that may be deferred until the relevant phase

Do not force premature decisions in Phase 0 when they do not affect the Phase 1 fixture slice.

These may be finalized later:

- exact live NSE discovery URLs/strategies,
- exact production backup transport,
- exact email provider,
- final disk forecasting formula,
- production Cloudflare settings,
- backfill UI defaults.

Each deferred decision must have a named "decision due before phase" entry in `current-state.md` or the risk register.

---

# 9. Canonical data baseline

## 9.1 Equity CSV

Locked columns:

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

Rules:

- only `series = EQ`,
- VWAP excluded,
- delivery quantity excluded,
- delivery percentage excluded.

## 9.2 CSV representation

Baseline already agreed in the planning handover:

```text
encoding: UTF-8 without BOM
delimiter: comma
newline: LF
final newline: required
null: literal NA
date: YYYY-MM-DD
column order: deterministic
row order: deterministic
floating point: do not serialize through binary-float artifacts
scientific notation: forbidden for canonical numeric fields
implicit rounding: forbidden
negative zero: normalize
trailing zeros: normalize according to locked numeric contract
generation timestamps: not inside market-data rows
```

Golden-file tests must lock byte output.

## 9.3 Package shapes

Daily:

```text
varys-market-data-YYYY-MM-DD.zip
  equity_market_data.csv
  index_ohlc.csv
  manifest.json
  preparation_report.csv
```

Universe, only when the selected snapshot changes:

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

## 9.4 Index CSV minimum baseline

The Phase 0 contract must lock the exact schema and optional-value semantics.
It must preserve the minimum approved product fields:

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

The historical handover statement that index turnover is excluded was a
planning inconsistency and is superseded by the higher-authority approved
specification. Phase 0 must define how unavailable volume/turnover values use
the canonical `NA` representation; it must not silently remove approved fields.

## 9.5 Universe CSV minimum baseline

The Phase 0 contract must lock the exact schema while preserving at least:

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

Only approved stable fields enter the canonical output. Additional source
columns remain available in immutable raw artifacts and cannot enter canonical
CSV output without a reviewed schema-version change.

## 9.6 HTTP surface baseline

Phase 0 API conventions must preserve the approved split:

```text
/             Angular frontend
/api/v1/*     JSON API and run/package metadata/control endpoints
/files/*      authenticated binary package downloads
```

Browser-controlled input must never resolve arbitrary filesystem paths.

---

# PHASE 0 — Foundation and contract lock

## 10.1 Outcome

Phase 0 creates a reproducible repository and runtime foundation that is strong enough for Phase 1 to implement a real fixture-driven vertical slice without re-litigating core architecture.

At Phase 0 exit:

- contracts exist,
- architecture boundaries exist,
- FastAPI and worker boot independently,
- PostgreSQL/Alembic work,
- durable storage primitives work,
- Angular shell builds,
- Docker Compose works,
- CI/testing foundations work,
- Codex state-management docs work.

Phase 0 does **not** implement the market-data product flow.

Traceability to the approved Phase 0 outcomes:

```text
0A         -> contracts
0B-0C      -> architecture, ADRs, repository, and tooling
0D         -> FastAPI and worker
0E         -> PostgreSQL and Alembic
0F         -> filesystem safety
0G         -> Angular shell
0H         -> Docker Compose runtime
0I         -> tests and CI
0J         -> Codex workflow and repository state
acceptance -> phase acceptance and handoff
```

The implementation iterations refine the ten approved Phase 0 outcomes;
they do not expand Phase 0 product scope.

## 10.2 Iteration 0A — Contracts

Create and review:

```text
docs/contracts/csv-representation-v1.md
docs/contracts/equity-csv-v1.md
docs/contracts/index-csv-v1.md
docs/contracts/universe-csv-v1.md
docs/contracts/manifest-v1.md
docs/contracts/preparation-report-v1.md
docs/contracts/run-state-model-v1.md
docs/contracts/package-state-model-v1.md
docs/contracts/source-adapter-v1.md
docs/contracts/api-conventions-v1.md
docs/contracts/configuration-v1.md
docs/contracts/filesystem-layout-v1.md
```

Acceptance:

- every contract has a version,
- examples are valid,
- conflicting field definitions are eliminated,
- deterministic representation is explicit,
- index and universe schemas preserve the minimum approved fields in sections
  9.4 and 9.5,
- API conventions preserve `/api/v1/*` for JSON APIs and `/files/*` for
  authenticated binary downloads,
- Phase 1 has no unresolved output-contract ambiguity.

## 10.3 Iteration 0B — Architecture and repository structure

Create:

```text
docs/architecture/repository-structure.md
docs/architecture/module-boundaries.md
docs/architecture/runtime-topology.md
docs/architecture/decisions/ADR-001-postgresql-run-dispatch.md
docs/architecture/decisions/ADR-002-package-publication.md
```

Acceptance:

- single Python codebase is explicit,
- API/worker boundaries are explicit,
- no broker is present,
- no microservice split exists,
- no Nginx runtime dependency exists,
- filesystem/database responsibility boundary is explicit.

## 10.4 Iteration 0C — Python project and common developer commands

Create Python tooling, dependency management, lint/type/test configuration, and a stable root command interface.

Recommended root commands:

```text
make bootstrap
make format
make lint
make typecheck
make test
make test-unit
make test-integration
make test-golden
make test-e2e
make build
make compose-up
make compose-down
make compose-smoke
make check
```

Acceptance:

- commands are documented,
- clean checkout can bootstrap,
- local commands do not require hidden global Python packages,
- versions are captured in `docs/implementation/dependency-baseline.md`.

## 10.5 Iteration 0D — FastAPI and worker bootstrap

Implement:

- configuration loader,
- structured JSON logging,
- request ID foundation,
- FastAPI app startup,
- worker process startup,
- liveness endpoints,
- basic process-level tests.

Acceptance:

- app process starts,
- worker process starts independently,
- app does not start worker work in-process,
- logs are structured and redact secrets,
- `/api/health/live` returns the intended liveness response.

## 10.6 Iteration 0E — PostgreSQL and Alembic foundation

Implement:

- SQLAlchemy session infrastructure,
- Alembic configuration,
- migration compatibility check,
- database readiness check,
- PostgreSQL integration test harness.

Acceptance:

- clean database can migrate to head,
- readiness fails when PostgreSQL is unreachable,
- readiness fails when migration state is incompatible,
- integration tests run against PostgreSQL, not SQLite pretending to be PostgreSQL.

Do not create speculative product tables unless they are required for a proven Phase 0/1 baseline.

## 10.7 Iteration 0F — Filesystem safety primitives

Implement:

- approved storage path resolver,
- safe relative-path handling,
- SHA-256 helper,
- durable `.part` writer,
- file flush + `fsync`,
- atomic rename helper,
- destination-directory `fsync` where required,
- storage readiness check,
- failure tests.

Acceptance:

- path traversal is rejected,
- incomplete `.part` file never masquerades as complete,
- checksum is stable,
- atomic rename happens on the same filesystem,
- storage readiness detects unwritable/missing paths.

## 10.8 Iteration 0G — Angular shell

Implement:

- Angular standalone app,
- PrimeNG baseline,
- top-level layout,
- route placeholders,
- API client foundation,
- route/component tests.

Approved route areas:

```text
Dashboard
Daily Data
Historical Backfill
Files and Packages
Runs and Diagnostics
Settings and Users
```

Acceptance:

- Angular production build succeeds,
- shell renders,
- placeholders do not show fake market/run data,
- API base configuration is environment-safe.

## 10.9 Iteration 0H — Docker image and Compose

Implement:

- multi-stage application Dockerfile,
- one image for app and worker,
- Compose services for app/worker/postgres,
- optional local `cloudflared` profile disabled by default,
- Angular production bundle served by FastAPI,
- persistent data volume/layout,
- Compose smoke test.

Acceptance:

```bash
docker compose build
docker compose up -d
docker compose ps
```

must demonstrate:

- app healthy,
- worker started,
- PostgreSQL internal,
- app and worker use the same image,
- Angular loads from the app service,
- no separate Nginx container,
- cloudflared not required for normal local startup.

## 10.10 Iteration 0I — Test and CI baseline

Establish:

- pytest layers,
- PostgreSQL integration tests,
- golden-test location,
- failure-injection test location,
- Angular lint/unit pipeline,
- Playwright skeleton,
- Docker Compose smoke job,
- Python lint/format/type checks,
- dependency scan,
- container-image scan,
- network prohibition for normal tests.
- GitHub Actions triggers for pushes to `main`; temporary-branch validation is
  added only when the owner explicitly requests it.

Acceptance:

- CI never calls live NSE,
- a test intentionally attempting uncontrolled network access fails,
- CI can build the production image,
- CI can run Compose smoke testing,
- required checks are documented.

## 10.11 Iteration 0J — Codex workflow/state documentation

Create:

```text
docs/ai/START_HERE.md
docs/ai/AGENT_WORKFLOW.md
docs/implementation/current-state.md
docs/implementation/risk-register.md
docs/implementation/definition-of-done.md
docs/implementation/dependency-baseline.md
docs/implementation/phases/phase-0.md
```

`AGENTS.md` must direct Codex to these files rather than duplicating the entire architecture.

Acceptance:

- fresh Codex session can identify the correct current phase,
- fresh session knows how to run tests,
- fresh session knows it cannot approve a phase,
- repository state and phase evidence provide the complete progress ledger,
- current-state is factual and matches repository behavior.

## 10.12 Phase 0 acceptance suite

From a clean checkout:

1. Bootstrap documented host/project prerequisites.
2. Build application image.
3. Start Compose stack.
4. Apply migrations to a clean database.
5. Verify liveness/readiness.
6. Verify Angular production shell is served.
7. Run Python unit tests.
8. Run PostgreSQL integration tests.
9. Run storage primitive/failure tests.
10. Run Angular tests.
11. Run Playwright bootstrap/smoke.
12. Run Docker Compose smoke test.
13. Run dependency/container scans.
14. Verify CI contains no live NSE access.
15. Verify contracts, ADRs, AI workflow docs, and state docs are present and consistent.
16. Review dependency and architecture drift.

Required evidence in `phase-0.md`:

- exact commit,
- exact commands,
- pass/fail results,
- Docker image identifier,
- Alembic revision,
- known warnings,
- deviations,
- open risks.

### Phase 0 stop condition

When all acceptance criteria pass, set:

```text
Status: USER_APPROVAL_PENDING
Owner approved: no
```

Do not begin Phase 1 until the owner explicitly approves Phase 0.

---

# PHASE 1 — Fixture-based daily vertical slice

## 11.1 Outcome

Deliver the first real end-to-end Varys workflow without live NSE dependency:

```text
create admin
  -> login
  -> choose fixture trading date
  -> create daily run
  -> worker claims run
  -> fixture adapters acquire controlled source artifacts
  -> parsers produce canonical rows
  -> package is generated and verified
  -> package is atomically published
  -> authenticated user downloads checksum-valid package
```

This phase proves the architecture before introducing live-source instability.

Traceability to the eight approved Phase 1 outcomes:

```text
1A         -> authentication and protected access
1B         -> runs, claims, leases, and recovery
1C         -> fixture adapters and workspaces
1D         -> parsers and canonical writers
1E-1F      -> package publication and failure matrix
1G         -> run and package APIs
1H-1I      -> daily UI and real-stack Playwright coverage
acceptance -> fixture acceptance and handoff
```

The nine implementation iterations split reliability and E2E verification out
for reviewability; they do not create a ninth Phase 1 product outcome.

## 11.2 Iteration 1A — Authentication and protected access

Implement:

- users table,
- auth sessions table,
- Argon2id password hashing,
- `varys create-admin`,
- login,
- logout,
- current-user endpoint,
- server-side session validation,
- secure cookie behavior,
- `HttpOnly`, `Secure`, and `SameSite=Lax` cookie flags,
- 12-hour idle timeout and 7-day absolute session lifetime,
- CSRF protection,
- route/API protection,
- session revocation.

Acceptance tests:

- create-admin creates a usable enabled user,
- plaintext passwords never appear in DB/logs,
- login rotates session,
- logout revokes session,
- protected API rejects unauthenticated requests,
- CSRF is required where designed,
- expired session is rejected,
- disabled user/session behavior matches contract.

## 11.3 Iteration 1B — Run persistence, events, claiming, leases

Implement:

- run persistence,
- append-only run events,
- one-active-run database enforcement,
- transactional worker claim,
- worker ID,
- lease expiry,
- heartbeat,
- expired-lease recovery,
- requested pause/cancel controls,
- safe terminal transitions.

Acceptance tests:

- two workers cannot claim the same run,
- only one active run total,
- expired lease can be recovered,
- active lease cannot be stolen,
- events are append-only,
- pause/cancel occur only at safe checkpoints,
- restart does not duplicate successful work.

## 11.4 Iteration 1C — Fixture source adapters and workspaces

Implement fixture versions of:

```text
Nifty500UniverseSource
CapitalMarketBhavcopySource
IndexReportSource
```

The fixture adapters must honor the same source-adapter contract later used for live implementations.

Implement isolated workspace:

```text
/data/work/<run-id>/
```

Acceptance:

- each run has isolated workspace,
- work files are not downloadable,
- fixture discovery/download/classify/verify use common interface,
- adapters do not own run-state transitions,
- adapters do not own retry orchestration,
- adapters do not publish packages.

## 11.5 Iteration 1D — Parsers and canonical writers

Implement:

- common CSV writer,
- schema guards,
- legacy Capital Market parser,
- UDiFF Capital Market parser,
- index parser,
- universe parser,
- EQ filtering,
- Decimal-safe numeric representation,
- deterministic sorting,
- explicit schema-change failure.

Acceptance:

- legacy and UDiFF fixtures map to equivalent canonical equity semantics,
- non-EQ rows are absent,
- VWAP/delivery fields are absent,
- future unexpected columns do not silently enter canonical output,
- malformed required fields fail safely,
- golden files are byte-identical across repeated runs.

## 11.6 Iteration 1E — Manifest, preparation report, and package publication

Implement:

- generated package metadata,
- generated package file metadata,
- manifest writer,
- preparation report writer,
- deterministic archive generation policy,
- `.zip.part` staging,
- reopen/verify archive,
- verify every member,
- atomic ready rename,
- checksum/size persistence,
- DB readiness transaction,
- startup reconciliation.

Acceptance:

- no `.part` member enters a ready package,
- manifest filenames match archive,
- checksums match,
- row counts match,
- duplicate business keys are rejected,
- archive reopens and every member is readable,
- DB never claims READY before final immutable file exists,
- ready archive is immutable,
- regeneration produces a new package identity.

## 11.7 Iteration 1F — Publication failure matrix

Inject failures:

- during generated CSV write,
- after CSV verify,
- during ZIP generation,
- after ZIP final rename but before DB readiness commit,
- after DB commit,
- during reconciliation.

Every case must prove:

```text
No partial package is downloadable.
No malformed package is READY.
No READY package is overwritten.
Interrupted work resumes or safely rebuilds.
```

## 11.8 Iteration 1G — Daily run and package APIs

Baseline API behavior:

- authenticated JSON API namespace under `/api/v1`,
- `POST /api/v1/runs/daily` accepts only `trade_date` and returns `202`,
- read run,
- read paginated run events,
- request pause/resume/cancel when valid,
- list/read package metadata,
- authenticated package download under `/files/*`.

The daily-run create request should accept only the inputs required by the contract, starting with `trade_date`.

Acceptance:

- create returns asynchronous acceptance behavior,
- duplicate conflicting active run returns `409` with
  `RUN_ALREADY_EXISTS`,
- APIs never expose absolute filesystem paths,
- invalid state transitions are rejected,
- package download checks state,
- package download checks final relative path,
- package download checks size,
- package download checks SHA-256 before streaming.

## 11.9 Iteration 1H — Minimal daily UI

Implement:

- login page,
- authenticated shell,
- daily trading-date selection,
- start-run action,
- run stage/status display,
- event display,
- warnings/errors display,
- package-ready display,
- download action only when valid.

Acceptance:

- UI uses real API,
- no mocked business state in real-stack E2E,
- refresh recovers current state from server,
- download remains unavailable for incomplete package,
- authentication boundary works.

## 11.10 Iteration 1I — Playwright vertical-slice acceptance

Critical E2E:

```text
clean database
  -> create admin
  -> browser login
  -> start fixture daily run
  -> observe progress
  -> package reaches READY/READY_WITH_WARNINGS
  -> download archive
  -> verify archive and checksum
```

Additional E2E:

- unauthenticated download blocked,
- incomplete package download blocked,
- logout invalidates access.

## 11.11 Phase 1 acceptance suite

From a clean checkout:

1. Build images.
2. Start clean Compose environment.
3. Run Alembic migrations.
4. Create first admin.
5. Log in through browser.
6. Run fixture-based daily workflow.
7. Prove worker transactional claim.
8. Prove one-active-run rule.
9. Prove heartbeat/lease recovery.
10. Produce deterministic canonical files.
11. Compare golden outputs.
12. Verify final ZIP and manifest/checksums.
13. Download package through authenticated endpoint.
14. Verify downloaded checksum.
15. Run publication failure matrix.
16. Restart app/worker during controlled run and prove safe recovery.
17. Run full Playwright login-to-download flow.
18. Run full CI suite.
19. Review architecture/dependency drift.
20. Update current-state, risk register, and Phase 2 prerequisites.

### Phase 1 stop condition

When all acceptance criteria pass:

```text
Status: USER_APPROVAL_PENDING
Owner approved: no
```

Do not begin Phase 2 until the owner explicitly approves Phase 1.

---

The Phase 2 through Phase 7 sections below are phase-level roadmap and
acceptance guardrails. They are intentionally not implementation-ready task
decompositions. Each later phase must be expanded only after the prior
phase is owner-approved and the actual repository baseline is audited.

# PHASE 2 — Real NSE acquisition and immutable raw archive

## 12.1 Outcome

Replace fixture acquisition with production-capable live-source adapters while preserving the Phase 1 parser/package pipeline.

Implement live versions of:

```text
Nifty500UniverseSource
CapitalMarketBhavcopySource
IndexReportSource
```

Also implement:

- persistent HTTP session,
- cookie persistence,
- NSE session bootstrap,
- browser-compatible request profile,
- request pacing,
- retries,
- session refresh,
- response classification,
- per-source circuit breaker,
- immutable content-addressed raw archive,
- source metadata/conflict detection,
- sanitized diagnostics.

Locked defaults:

```text
network concurrency: 1
base delay: 4 seconds
random extra delay: 1-3 seconds
transient retries: 3
session refresh attempts/file: 2
```

Response classifications:

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

## 12.2 Phase 2 acceptance tests

Automated CI must use controlled fixtures/mocked HTTP and prove:

- every response classification,
- 200 HTML challenge is not accepted as a file,
- zero/truncated/corrupt content rejected,
- wrong trade date rejected,
- schema change rejected,
- transient retry count bounded,
- session refresh bounded,
- 429 cooldown behavior,
- 403/challenge opens source circuit,
- open circuit stops automated acquisition,
- HALF_OPEN controlled test behavior,
- raw SHA-256 content addressing,
- identical bytes deduplicate,
- conflicting bytes for same logical source/date create conflict record,
- raw artifact is immutable.

A manually initiated deployed diagnostic may perform a controlled live NSE request. It is not part of normal CI.

### Phase 2 stop condition

`USER_APPROVAL_PENDING`, never self-approved.

---

# PHASE 3 — Production daily operations

## 13.1 Outcome

Make daily operation reliable and largely unattended.

Implement:

- official/imported NSE holiday calendar,
- weekend filtering,
- actual report availability,
- daily scheduler inside worker,
- PostgreSQL scheduler locking,
- missed-run recovery,
- 20:00 IST first attempt,
- 30-minute retry interval,
- 23:30 IST cutoff,
- `WAITING_FOR_SOURCE`,
- no prior-day substitution,
- universe snapshot change detection,
- immutable universe package only on change,
- daily package retention,
- operator dashboard,
- required email alerts.

Required alert conditions:

- daily run not completed by cutoff,
- source circuit opened,
- missing worker heartbeat,
- repeated run failure,
- low disk,
- backup failure,
- package reconciliation failure.

## 13.2 Phase 3 acceptance tests

Use simulated clocks and fixture sources to prove:

- scheduler creates one equivalent run only,
- restart does not duplicate schedule,
- missed schedule is detected,
- time zone is Asia/Kolkata,
- retry timing follows configuration,
- cutoff produces `WAITING_FOR_SOURCE`,
- prior-day data is never substituted,
- unexplained weekday gap remains visible,
- unchanged universe does not publish duplicate universe package,
- changed universe publishes a new immutable package,
- retention never removes permanent raw/universe/backfill artifacts,
- all alert conditions can be triggered in tests,
- dashboard reflects real persisted operational state.

### Phase 3 stop condition

`USER_APPROVAL_PENDING`, never self-approved.

---

# PHASE 4 — Historical backfill

## 14.1 Outcome

Implement resumable historical preparation for approximately five years using the selected current Nifty 500 snapshot.

Flow:

```text
freeze universe snapshot
  -> expected trading dates
  -> reuse verified cached sources
  -> acquire missing equity sequentially
  -> acquire missing index sequentially
  -> checkpoint every verified source
  -> classify gaps
  -> prepare yearly equity chunks
  -> retry unresolved dates
  -> publish only when blocking gaps resolved
```

Batch/report checkpoint size:

```text
100 downloads
```

Network concurrency remains one.

Year chunk states:

```text
BUILDING
VERIFIED
FAILED
```

Dependency fingerprint includes:

- source checksums,
- universe snapshot ID,
- parser version,
- output schema version,
- configuration fingerprint.

## 14.2 Phase 4 acceptance tests

Prove with a bounded fixture backfill:

- selected universe stays frozen,
- expected trading-date list is deterministic,
- cached verified files are reused,
- acquisition remains sequential,
- checkpoint survives worker restart,
- pause/resume works at safe boundaries,
- cancel is safe,
- unresolved blocking dates prevent final publication,
- yearly verified chunk is reused only when fingerprint matches,
- changed dependency invalidates affected chunk,
- completed backfill package is deterministic and immutable,
- one-active-run rule still applies.

### Phase 4 stop condition

`USER_APPROVAL_PENDING`, never self-approved.

---

# PHASE 5 — Repair and conflict workflows

## 15.1 Outcome

Give the operator controlled ways to recover from real source failures without bypassing validation.

Implement:

- repair runs,
- `SecurityWiseRepairSource`,
- replacement raw-file upload,
- one-date source URL override,
- retry discovery,
- cached source invalidation,
- conflicting version selection,
- resume from failed date,
- audit events,
- package supersession/versioning.

Every manually supplied file passes the same technical checks as automated acquisition.

## 15.2 Phase 5 acceptance tests

Prove:

- manual upload cannot bypass archive/date/schema validation,
- URL override applies only to intended date/scope,
- invalidated file is never silently reused,
- conflict selection is explicit and audited,
- repair source follows common adapter contract,
- resume starts from safe failed boundary,
- old ready package remains immutable,
- repaired publication creates new package version,
- all sensitive operator actions generate audit events,
- audit logs contain no passwords/tokens/cookies.

### Phase 5 stop condition

`USER_APPROVAL_PENDING`, never self-approved.

---

# PHASE 6 — Private production deployment

## 16.1 Outcome

Deploy Varys privately with reproducible images, perimeter access control, backups, health checks, and rollback.

Implement:

- GHCR immutable image publication,
- production Compose hardening,
- Cloudflare Tunnel,
- Cloudflare Access,
- Varys login still mandatory,
- secrets outside Git,
- non-root containers where practical,
- no public PostgreSQL/worker/filesystem/Docker socket,
- manual deployment approval,
- pre-deploy PostgreSQL backup,
- disk check,
- Alembic migration step,
- app/worker restart,
- health/smoke checks,
- rollback to prior image,
- nightly logical database backup,
- encrypted off-VPS backup,
- raw and ready package backup policy.

Never back up:

```text
/data/work
/data/packages/staging
```

## 16.2 Phase 6 acceptance tests

From the target production topology prove:

- public access reaches Cloudflare Access first,
- bypassing Cloudflare does not expose FastAPI directly,
- Varys login is still required after Cloudflare Access,
- PostgreSQL has no public listener,
- worker has no public listener,
- package filesystem cannot be directly browsed,
- deployment uses immutable image tag/digest,
- pre-deploy backup completes,
- migration succeeds,
- health checks pass,
- fixture production smoke run succeeds,
- rollback to previous image works,
- nightly backup artifact is produced and encrypted off-host,
- excluded work/staging paths are not backed up.

### Phase 6 stop condition

`USER_APPROVAL_PENDING`, never self-approved.

---

# PHASE 7 — Hardening and V1 release acceptance

## 17.1 Outcome

Close reliability/security gaps and prove V1 readiness against the complete approved architecture.

Implement/finalize:

- authenticated user administration,
- create/enable/disable/reset password/view last login,
- password-reset session revocation,
- disabled-user session revocation,
- login throttling,
- download throttling,
- security headers,
- full failure-injection matrix,
- low-disk behavior,
- alert verification,
- quarterly restore drill procedure,
- V1 release checklist.

## 17.2 Phase 7 acceptance tests

Required final checks include:

- all required CI checks green,
- migrations succeed from supported prior state,
- app/worker health green,
- unauthorized access blocked,
- login works,
- disabled user loses access,
- password reset revokes old sessions,
- throttling works,
- fixture daily generation succeeds,
- deterministic golden tests pass,
- package checksum validation succeeds,
- incomplete package download rejected,
- no READY package is malformed,
- failure matrix proves safe recovery,
- low disk produces safe pause/failure behavior,
- all alert paths tested,
- backup state healthy,
- full restore into temporary environment succeeds,
- selected raw checksums verify after restore,
- at least one restored ready package reopens and validates,
- previous deployable image remains available,
- production Cloudflare Access + Varys login both verified,
- change-triggered universe package behavior verified,
- `SecurityWiseRepairSource` workflow verified.

### Phase 7 stop condition

When release acceptance is green:

```text
Status: USER_APPROVAL_PENDING
Owner approved: no
```

Only the owner may declare V1 approved/released.

---

# 18. Definition of Done

## 18.1 Implementation iteration Done

An iteration is done only when:

- scoped code/docs are implemented,
- relevant tests were added/updated,
- relevant tests pass,
- diff was reviewed against scope,
- no unrelated cleanup was mixed in,
- new dependencies are justified,
- contracts/ADRs were updated when behavior changed,
- current phase state was updated,
- known limitations are documented.

This does not imply phase completion.

## 18.2 Phase acceptance-ready

A phase may enter `USER_APPROVAL_PENDING` only when:

- all planned phase acceptance criteria pass,
- clean-environment or equivalent reproducibility test passes,
- CI is green for required jobs,
- architecture/dependency drift was reviewed,
- current-state is updated,
- risk register is updated,
- deviations are documented,
- unresolved limitations are explicit,
- next-phase prerequisites are explicit,
- evidence contains exact commit and commands.

## 18.3 Phase approved

A phase is `APPROVED` only after explicit owner instruction.

Tests passing are necessary but not sufficient.

Codex must not write an approval statement on the owner's behalf.

## 18.4 V1 release approved

V1 is approved only when:

- Phase 0 through Phase 7 are owner-approved,
- release acceptance passes,
- production topology is verified,
- backup/restore evidence exists,
- owner explicitly approves release.

---

# 19. Risk register baseline

Maintain these in `docs/implementation/risk-register.md`.

## R1 — NSE source instability

Risk:

- URLs change,
- headers/cookies change,
- HTML challenge returned with HTTP 200,
- schema changes,
- publication delay.

Controls:

- source adapters,
- content validation,
- classification,
- bounded retry/session refresh,
- circuit breaker,
- diagnostics,
- manual repair,
- no live NSE dependency in CI.

## R2 — Parser/schema drift

Risk:

- silent bad canonical output.

Controls:

- explicit schema detection,
- parser version identifiers,
- contract versions,
- golden files,
- fail on unknown schema.

## R3 — Partial file / package corruption

Controls:

- `.part`,
- fsync,
- reopen/verify,
- checksums,
- atomic rename,
- DB READY after file finalization,
- startup reconciliation,
- failure injection.

## R4 — Worker crash / duplicate work

Controls:

- PostgreSQL transactional claim,
- one-active-run rule,
- lease,
- heartbeat,
- checkpoints,
- idempotent reuse,
- recovery tests.

## R5 — Storage growth

Controls:

- permanent scope clearly limited,
- configurable daily package retention,
- disk threshold,
- dashboard alert,
- backfill/disk estimation before large work.

## R6 — Authentication/session mistakes

Controls:

- Argon2id,
- server-side revocable sessions,
- secure cookie,
- CSRF,
- throttling,
- generic errors,
- session rotation/revocation tests.

## R7 — Production deployment/backup failure

Controls:

- immutable image,
- manual approval,
- pre-deploy backup,
- health checks,
- rollback,
- off-VPS encryption,
- restore verification.

## R8 — AI-agent scope drift

Risk:

- Codex expands scope,
- changes architecture to solve local issue,
- weakens tests,
- prematurely claims completion.

Controls:

- AGENTS.md,
- phase state machine,
- bounded phase scope,
- owner-only approval,
- ADR requirement,
- diff review,
- acceptance evidence.

---

# 20. AGENTS.md guidance

Keep `AGENTS.md` concise. It should point to source documents rather than duplicate them.

Suggested content:

```markdown
# Varys agent instructions

Read before editing:
1. docs/implementation/implementation-plan.md
2. docs/implementation/varys_requirements_and_architecture_spec.md
3. docs/implementation/varys_gpt56_implementation_planning_handoff.md
4. docs/implementation/varys_llm_handover_pre_implementation.md
5. docs/implementation/current-state.md
6. current phase file under docs/implementation/phases/
7. relevant docs/contracts/
8. relevant docs/architecture/decisions/

Rules:
- Do not redesign locked architecture without explicit owner approval and an ADR.
- Do not use live NSE in normal CI.
- Do not run long work inside FastAPI request handlers.
- Preserve one app image shared by app and worker.
- Preserve PostgreSQL-backed run claiming; do not add Redis/Celery/etc.
- Raw files and ready packages are immutable.
- No partial package may be downloadable.
- Run relevant tests after edits.
- Update current-state and current phase evidence.
- Use main by default through the first V1 release. Use a temporary branch only
  when the owner explicitly requests one for a specific need.
- Never set a phase to APPROVED. Stop at USER_APPROVAL_PENDING.
```

Nested `AGENTS.override.md` files should be added only if a directory genuinely needs different instructions.

---

# 21. New-chat prompt template for each phase

Use this at the beginning of every new phase chat:

```text
We are implementing Varys Phase <N>.

Do not rely on any previous chat memory.

First read:
- AGENTS.md
- docs/implementation/implementation-plan.md
- docs/implementation/varys_requirements_and_architecture_spec.md
- docs/implementation/varys_gpt56_implementation_planning_handoff.md
- docs/implementation/varys_llm_handover_pre_implementation.md
- docs/implementation/current-state.md
- docs/implementation/phases/phase-<N>.md
- relevant contracts
- relevant ADRs
- risk register
- dependency baseline
- definition of done, if present

Then inspect the actual Git repository state and run the smallest appropriate baseline checks.

Use main as the default working branch through the first V1 release. Use a
temporary branch only when the owner explicitly requests one for a specific
risk, experiment, or review boundary. Treat historical default-branch
instructions in planning handoffs as superseded.

Before editing, report:
1. verified baseline and commit,
2. current phase status,
3. exact scope for the next implementation iteration,
4. files/modules you expect to touch,
5. tests you will run,
6. risks/assumptions,
7. anything that conflicts with the plan.

Implement iteratively. Update phase state and current-state as evidence changes.

Do not mark the phase APPROVED or DONE. When every acceptance test passes, set the phase only to USER_APPROVAL_PENDING and wait for my explicit approval.
```

---

# 22. Per-iteration Codex prompt template

For work inside a phase:

```text
Continue Phase <N>, Iteration <X>.

Verify repository state first.

Implement only:
<scope>

Acceptance criteria:
<criteria>

Out of scope:
<explicit exclusions>

Required tests:
<commands or test groups>

After implementation:
- review the diff,
- run required tests,
- update the phase evidence,
- update current-state if capabilities changed,
- record deviations/limitations,
- do not mark the phase approved.
```

---

# 23. Phase review checklist for the owner

Before approving any phase, review:

- Does the implementation match the locked architecture?
- Did Codex add an unnecessary service/dependency?
- Are migrations safe?
- Are secrets excluded?
- Are raw/ready immutability rules preserved?
- Can a partial package become downloadable?
- Are tests proving failure behavior, not just happy path?
- Are outputs deterministic?
- Are state docs truthful?
- Are known limitations acceptable?
- Does the next phase have a clean entry state?

Only after this review should the owner explicitly approve the phase.

---

# 24. Release acceptance summary

The complete V1 is expected to prove:

```text
fixture path:
login -> daily run -> deterministic package -> authenticated download

live path:
NSE -> validated immutable raw source -> deterministic package -> authenticated download

operations:
scheduler -> retries -> waiting/circuit behavior -> diagnostics -> repair

backfill:
frozen universe -> resumable historical processing -> immutable package

deployment:
Cloudflare Access -> Varys login -> private Compose runtime

recovery:
crash/partial file/state mismatch -> no corrupt READY package -> resume/rebuild/quarantine

backup:
nightly protected backup -> periodic restore verification
```

The architecture is intentionally simple enough for one developer but must still behave like a production data-acquisition system.

---

# 25. Initial action after adding this file to the repository

Do not start coding Phase 0 immediately.

Run Pre-Phase first:

1. verify Ubuntu,
2. install/verify Git and base CLI tools,
3. install/verify Docker Engine + Compose,
4. install/verify Codex,
5. create/verify `AGENTS.md`,
6. create/verify `.codex/config.toml`,
7. create truthful `current-state.md`,
8. create `pre-phase.md`,
9. run Pre-Phase acceptance checks,
10. stop at `USER_APPROVAL_PENDING`.

After explicit owner approval, start a **new Codex chat** for Phase 0.

---

## Appendix A — Locked run states

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

`WAITING_FOR_SOURCE`, `PAUSED`, and `SOURCE_BLOCKED` retain the single-active-run slot unless an approved contract explicitly refines that behavior.

---

## Appendix B — Locked package states

```text
BUILDING
VERIFYING
READY
READY_WITH_WARNINGS
FAILED
QUARANTINED
SUPERSEDED
```

Download rule:

```text
status in (READY, READY_WITH_WARNINGS)
AND final file exists
AND size matches metadata
AND SHA-256 matches metadata
```

---

## Appendix C — Durable package publication rule

```text
DB package row BUILDING
  -> write generated files in isolated workspace
  -> verify generated files
  -> create staging ZIP.part
  -> flush + fsync
  -> reopen ZIP
  -> verify every member
  -> atomic rename into ready directory
  -> fsync destination directory
  -> DB transaction records path/size/checksum/files
  -> package READY / READY_WITH_WARNINGS
  -> run completed
```

Crash cases must remain recoverable:

```text
before final rename:
  package unavailable; resume/rebuild

after rename but before DB commit:
  file exists but is unavailable until reconciliation

after DB commit:
  package remains downloadable if validation still succeeds
```

---

## Appendix D — Backfill dependency fingerprint

A verified yearly chunk is reusable only if this fingerprint still matches:

```text
source-file checksums
universe snapshot ID
parser version
output schema version
configuration fingerprint
```

---

## Appendix E — Human approval phrase

There is no required magic wording, but the instruction must be unambiguous.

Examples:

```text
I approve Phase 0.
Mark Phase 0 approved and proceed to Phase 1 planning.
Phase 1 is accepted.
```

Absent explicit owner approval, the highest valid state remains:

```text
USER_APPROVAL_PENDING
```
