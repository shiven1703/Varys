# Filesystem Layout Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

`VARYS_DATA_ROOT` is an absolute, configured directory. All managed paths are
relative to it:

```text
raw/sha256/<first-two-hex>/<sha256>
work/<run-id>/
packages/staging/<package-id>.zip.part
packages/ready/daily/<package-id>.zip
packages/ready/universe/<package-id>.zip
packages/ready/backfill/<package-id>.zip
quarantine/
diagnostics/
```

Only canonical UUIDs may form `run-id` and `package-id`; only a verified
lowercase SHA-256 may form a raw-artifact name. Resolve every managed path and
reject paths outside its approved root, absolute child paths, `.`/`..`, path
separators in identifiers, and symlinks that escape the root. Browser input
never selects a filesystem path.

Raw artifacts and ready packages are immutable. Work and staging are temporary
and never downloadable. Durable output writes use a sibling `.part` file,
flush, file `fsync`, close/reopen verification, same-filesystem atomic rename,
and destination-directory `fsync`. The database records a ready package only
after its immutable final archive exists and has been verified.
