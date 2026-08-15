# Risk Register

Status: active Phase 0 ledger. Update when risk status, evidence, or mitigation
changes.

| ID | Risk | Status | Mitigation / evidence | Exit condition |
| --- | --- | --- | --- | --- |
| R-001 | Current Codex session cannot access Docker daemon. | Managed | The session limitation remains, but successful main CI completed the Phase 0 build, Compose, browser, and image-scan checks. | Use CI evidence for Docker validation until a daemon-enabled Codex session is available. |
| R-002 | Clean PostgreSQL migration/readiness has no live evidence for the latest migration. | Open | Host-terminal `make compose-smoke` migrated a clean Compose database to `0003_run_dispatch`; all four PostgreSQL integration tests and health checks passed. Migrations `0004_package_publication` and `0005_daily_run_trade_date` render successfully and have fixture integration coverage, but no live PostgreSQL evidence in this Codex session. | Run clean Compose smoke or CI against `0005_daily_run_trade_date`, including package publication/reconciliation and authenticated API integration coverage. |
| R-003 | GitHub Actions and Trivy have not executed remotely. | Closed | Successful Phase 0 main CI completed the sequential job. Trivy retains a HIGH/CRITICAL gate with two third-party-SBOM-only suppressions expiring 2026-09-15; Gitleaks owns secret scanning. | Reopen if CI fails or the suppressions require review. |
| R-004 | Container and frontend builds may pressure the 7.2 GiB host. | Open | Builds are multi-stage and dependencies are pinned. | Record successful monitored Docker build on target host. |
| R-005 | Public repository could receive a credential in a future commit. | Managed | Tracked files and reachable history have no high-confidence credential or private-key match; Gitleaks scans full history on `main` pushes. | Review each secret-scan failure and rotate/remove any real credential. |
| R-006 | Authentication/session defects could retain unauthorized access or expose a credential. | Managed | Argon2id hashes only; session and CSRF secrets are opaque token hashes stored server-side; login rotates, logout revokes, expiry and disabled-user rejection are implemented. The owner accepted Iteration 1A; PostgreSQL integration remains Phase 1 acceptance evidence. | Pass clean-PostgreSQL authentication integration and Docker validation before Phase 1 acceptance. |
