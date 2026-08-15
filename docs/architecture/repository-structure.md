# Repository Structure

Status: Phase 0 Iteration 0B. This is the target structure; directories are
created only by the iteration that implements them.

```text
AGENTS.md
README.md
Makefile
pyproject.toml
uv.lock
docker/
  Dockerfile
  entrypoints/
compose.yaml
backend/
  varys/
    api/
    auth/
    config/
    db/
    domain/
    health/
    logging/
    packages/
    runs/
    sources/
    storage/
    worker/
  tests/
    unit/
    integration/
    golden/
    failure_injection/
    fixtures/
frontend/
  src/app/
  e2e/
migrations/
  versions/
docs/
  architecture/
  contracts/
  implementation/
scripts/
  ci/
  dev/
  maintenance/
.github/workflows/
```

`backend/varys` is the single Python application codebase. The FastAPI process
and worker import it and differ only by startup command. `backend/tests` owns
all Python fixtures and deterministic test layers; `frontend/e2e` owns browser
tests. Alembic migration code is top-level because it evolves the operational
database, while application models remain in `backend/varys/db`.

`docs/contracts` defines versioned public and data boundaries. `docs/architecture`
records long-lived structure and ADRs. Runtime data never belongs in the Git
worktree; it is stored under the configured data root described by the
filesystem contract.
