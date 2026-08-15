# ADR-001: PostgreSQL-Backed Run Dispatch

Status: Accepted

## Context

Varys has long-running acquisition, parsing, backfill, repair, and package
regeneration work. V1 permits exactly one active run total and must recover
after worker failure without a separate broker.

## Decision

Use PostgreSQL as the run-dispatch authority. The API creates and controls run
records; the dedicated worker claims eligible work transactionally using row
locking, records a lease and heartbeats while running, and checkpoints safe
progress. Expired leases are recoverable by worker reconciliation. The worker
also hosts the daily scheduler and uses PostgreSQL locking to prevent duplicate
scheduling.

`RUNNING`, `WAITING_FOR_SOURCE`, `PAUSED`, and `SOURCE_BLOCKED` retain the
single active-run slot. Additional work remains queued. API request handlers do
not execute long-running work.

## Consequences

This keeps operational state, locking, and recovery in one already-required
service and preserves a simple two-process application model. It requires
careful transactional claiming, lease expiry, heartbeat, and integration tests.
Redis, RabbitMQ, Celery, Kafka, and a separate scheduler are explicitly out of
scope unless the owner reopens this decision through a new ADR.
