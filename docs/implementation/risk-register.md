# Risk Register

Status: active Phase 0 ledger. Update when risk status, evidence, or mitigation
changes.

| ID | Risk | Status | Mitigation / evidence | Exit condition |
| --- | --- | --- | --- | --- |
| R-001 | Current Codex session cannot access Docker daemon. | Open | Docker config validates; build, Compose, browser, and image-scan execution are deferred by owner approval. | Run documented Docker and Playwright checks with daemon access. |
| R-002 | Clean PostgreSQL migration/readiness has no live evidence. | Open | Integration harness exists and skips without `VARYS_TEST_DATABASE_URL`; Compose smoke invokes it in CI. | Run it successfully against a clean PostgreSQL database. |
| R-003 | GitHub Actions, pip-audit, and Trivy have not executed remotely. | Open | Workflow is main-only and commands are pinned/documented; local production npm audit passes. | Observe successful main workflow runs. |
| R-004 | Container and frontend builds may pressure the 7.2 GiB host. | Open | Builds are multi-stage and dependencies are pinned. | Record successful monitored Docker build on target host. |
| R-005 | Public repository could receive a credential in a future commit. | Managed | Tracked files and reachable history have no high-confidence credential or private-key match; Gitleaks scans full history on `main` pushes. | Review each secret-scan failure and rotate/remove any real credential. |
