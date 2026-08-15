# Configuration Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Configuration is loaded once at process startup from environment variables and
optionally an explicitly selected local environment file. Secrets are supplied
only through the runtime environment or secret mounts, never committed or
logged. Unknown `VARYS_` settings and invalid values fail startup.

The required configuration families are `VARYS_DATABASE_URL`,
`VARYS_DATA_ROOT`, session/security secrets, API bind settings, worker identity,
and environment mode. The configurable operational families are daily schedule
(`Asia/Kolkata`, first attempt `20:00`, retry `30m`, cutoff `23:30`), network
pacing (concurrency `1`, base delay `4s`, random delay `1-3s`, retries `3`),
session refresh attempts (`2`), backfill batch size (`100`), package retention,
disk threshold, universe refresh interval, request profile, and output schema
version.

Defaults above are locked V1 defaults, not browser-controlled inputs. A
configuration fingerprint is the lowercase SHA-256 of canonical JSON containing
only effective non-secret settings with sorted keys; it is recorded in package
provenance. Exact live NSE discovery URLs, backup transport, email provider,
and production Cloudflare settings remain deferred to their named later phases.
