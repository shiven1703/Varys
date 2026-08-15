# Package State Model Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Packages use exactly these states:

```text
BUILDING
VERIFYING
READY
READY_WITH_WARNINGS
FAILED
QUARANTINED
SUPERSEDED
```

Creation records `BUILDING`; complete staged outputs move to `VERIFYING`.
Successful verification and same-filesystem atomic publication transition to
`READY` or `READY_WITH_WARNINGS`. Verification failures transition to `FAILED`.
Reconciliation transitions a missing, corrupt, or inconsistent package to
`QUARANTINED`; a newer replacement may mark a previous ready package
`SUPERSEDED`. `READY`, `READY_WITH_WARNINGS`, `FAILED`, `QUARANTINED`, and
`SUPERSEDED` are terminal for that package version.

Download is allowed only for `READY` or `READY_WITH_WARNINGS` when the stored
relative path resolves inside the appropriate ready root, the file exists, its
size matches metadata, and its SHA-256 matches metadata. No `.part`, work, or
staging file is downloadable. A ready package is immutable; regeneration makes
a new package ID and version rather than overwriting it.
