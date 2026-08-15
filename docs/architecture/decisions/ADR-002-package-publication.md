# ADR-002: Recoverable Package Publication

Status: Accepted

## Context

Ready packages must be immutable and never partially downloadable. Filesystem
publication and a PostgreSQL transaction cannot be one ACID transaction, so a
crash at their boundary must be recoverable.

## Decision

Create a package record in `BUILDING` and write temporary outputs only in the
isolated run workspace. Build the final ZIP in package staging as `.part`,
flush and `fsync` it, reopen and verify every member and checksum, then rename
it atomically on the same filesystem into the appropriate immutable ready root
and `fsync` that directory. Only after the final archive exists does one
PostgreSQL transaction record its relative path, size, SHA-256, file metadata,
and `READY` or `READY_WITH_WARNINGS` state.

Downloads verify a ready state, approved relative path, existence, size, and
SHA-256. Startup reconciliation adopts or quarantines files left by a crash;
missing or corrupt ready packages receive one regeneration attempt when raw
inputs exist, then require quarantine/manual action.

## Consequences

The filesystem owns durable package bytes and PostgreSQL owns publication
visibility. Ready packages are never overwritten; regeneration produces a new
package ID, version, checksum, and manifest. This requires explicit failure
injection and reconciliation tests, but prevents partial or unverified
downloads without object storage or distributed transactions.
