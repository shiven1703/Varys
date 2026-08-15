# Module Boundaries

Status: Phase 0 Iteration 0B.

## Processes

The FastAPI process owns authenticated HTTP endpoints, run creation and control,
read-only run/source/package metadata, package-download authorization, health
endpoints, and serving the Angular production bundle. Request handlers enqueue
or control work only; they never acquire sources, parse data, backfill, or
generate packages.

The dedicated worker owns PostgreSQL run claiming, leases, heartbeats, the
in-process scheduler, acquisition and parser orchestration, package generation,
safe checkpointing, pause/cancel safe points, reconciliation, and recovery.

## Shared Python modules

`domain` owns typed domain values and state transitions. `config` owns validated
startup configuration. `db` owns SQLAlchemy models, repositories, transactions,
and Alembic integration. `storage` owns approved-path resolution and durable
file primitives. `sources` owns adapter interfaces and parser selection;
`packages` owns canonical writers, manifests, verification, and publication
coordination. `runs` owns run commands, events, and claim semantics. `auth`,
`health`, and `logging` own their respective cross-cutting concerns.

The API and worker use these shared modules rather than duplicating business
rules. `frontend` consumes only authenticated HTTP and download surfaces; it
does not receive database credentials or filesystem paths.

## Data boundaries

PostgreSQL contains operational metadata only: users, sessions, runs, events,
source metadata/conflicts, universe snapshots, package metadata/files,
settings, and audit events. It does not contain the market-data history or raw
artifacts. The filesystem contains immutable raw artifacts and ready packages,
plus temporary work/staging files. The database establishes intent and
visibility; filesystem helpers establish durable bytes.
