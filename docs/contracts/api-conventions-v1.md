# API Conventions Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

The Angular frontend is served at `/`. JSON endpoints live only below
`/api/v1/`; authenticated binary package downloads live only below `/files/`.
No JSON endpoint returns raw package bytes and no file endpoint accepts a
browser-provided filesystem path.

JSON requests and responses use UTF-8 `application/json`; successful JSON
responses use a documented 2xx status and validation errors use a stable 4xx
status with `{"detail": "..."}`. Dates are `YYYY-MM-DD`, timestamps are RFC
3339 UTC, and identifiers are opaque strings. Endpoints must authenticate
before exposing run, source, package, or diagnostic metadata; downloads also
require an enabled session and the package-state checks in the package contract.

Future routes derive package download targets from an opaque package ID stored
server-side. API version changes are additive within `v1` or require `/api/v2/`;
they do not silently change a canonical CSV contract.
