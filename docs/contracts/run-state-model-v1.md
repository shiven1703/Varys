# Run State Model Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Runs use exactly these states:

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

`QUEUED` is eligible for PostgreSQL-backed claiming. A successfully claimed
run enters `RUNNING` and records a worker ID, lease expiry, and heartbeat. A
worker may transition `RUNNING` to `WAITING_FOR_SOURCE`, `PAUSED`,
`SOURCE_BLOCKED`, `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED`, or
`CANCELLED`; `WAITING_FOR_SOURCE` may return to `RUNNING`; `PAUSED` may return
to `QUEUED`; and `SOURCE_BLOCKED` may return to `QUEUED` only after explicit
operator repair. Terminal states are `COMPLETED`, `COMPLETED_WITH_WARNINGS`,
`FAILED`, and `CANCELLED`.

V1 permits exactly one active run total. `RUNNING`, `WAITING_FOR_SOURCE`,
`PAUSED`, and `SOURCE_BLOCKED` retain that slot; queued work waits. State
changes, safe checkpoint progress, leases, and errors are recorded as ordered
run events. A worker never runs acquisition, parsing, or packaging in an API
request handler.
