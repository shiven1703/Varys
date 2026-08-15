# Varys

Varys prepares verified NSE/Nifty Indices market-data packages for manual upload
to Hodor. It does not connect to Hodor or run Hodor business workflows.

## Developer commands

Run `make bootstrap` once from a clean checkout. It creates `.venv` and installs
the pinned development tools from `requirements-dev.lock`; it does not require
global Python packages. Then use:

```text
make format
make lint
make typecheck
make test
make test-unit
make test-golden
make test-failure-injection
make test-e2e
make check
```

All listed Phase 0 developer commands are implemented. Docker-backed commands
require a Docker daemon and a local `.env` copied from `.env.example`.

## Frontend commands

The Angular shell has its own pinned npm workspace:

```text
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend test -- --watch=false
```

The production bundle is served by FastAPI in Iteration 0H; it is not served by
a separate frontend or Nginx runtime.

## Local runtime

Copy `.env.example` to `.env`, choose a local-only PostgreSQL password, then
run `make build` and `make compose-up`. The app is available only on
`http://127.0.0.1:8000`; PostgreSQL has no host port. `make compose-smoke`
builds, runs the PostgreSQL integration suite against the clean Compose
database, verifies, and removes the local Compose topology. Cloudflare Tunnel
is optional and disabled unless the `cloudflared` profile is selected with
`CLOUDFLARE_TUNNEL_TOKEN` set.

The first Docker build must download base images and pinned dependencies. Later
BuildKit builds reuse persistent npm and pip package caches; keep the Docker
builder cache unless disk space requires pruning it.

## CI checks

One sequential GitHub Actions job on pushes to `main` runs the Gitleaks
full-history scan, Python format/lint/type/unit/golden/failure tests, frontend
lint/unit/build, one Docker Compose build reused for smoke and Playwright,
dependency scans, and a Trivy image scan. Tests prohibit uncontrolled network
access; fixture or PostgreSQL integration tests are the explicit exceptions.

See `docs/implementation/implementation-plan.md` for the phase plan and
`docs/implementation/current-state.md` for the implementation ledger.
