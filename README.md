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
Phase 0 iteration: `test-integration` (0E), `test-golden` and `test-e2e` (0I),
and `build`, `compose-up`, `compose-down`, and `compose-smoke` (0H).

## Frontend commands

The Angular shell has its own pinned npm workspace:

```text
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend test -- --watch=false
```

The production bundle is served by FastAPI in Iteration 0H; it is not served by
a separate frontend or Nginx runtime.

See `docs/implementation/implementation-plan.md` for the phase plan and
`docs/implementation/current-state.md` for the implementation ledger.
