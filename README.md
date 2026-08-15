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
make check
```

The remaining stable targets are intentionally placeholders until their owning
Phase 0 iteration: `test-golden` and `test-e2e` (0I).

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
builds, verifies, and removes the local Compose topology. Cloudflare Tunnel is
optional and disabled unless the `cloudflared` profile is selected with
`CLOUDFLARE_TUNNEL_TOKEN` set.

See `docs/implementation/implementation-plan.md` for the phase plan and
`docs/implementation/current-state.md` for the implementation ledger.
