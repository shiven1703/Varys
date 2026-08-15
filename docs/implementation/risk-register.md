# Risk Register

Status: active Phase 1 ledger. Update when risk status, evidence, or mitigation
changes.

| ID | Risk | Status | Mitigation / evidence | Exit condition |
| --- | --- | --- | --- | --- |
| R-001 | Current Codex sandbox cannot access Docker daemon. | Managed | The sandbox limitation remains, but the owner terminal has direct Docker access and completed the clean Phase 1 build, Compose, PostgreSQL, restart, and browser checks. | Use owner-terminal and CI evidence for Docker validation until a daemon-enabled Codex session is available. |
| R-002 | Clean PostgreSQL migration/readiness has no live evidence for the latest migration. | Closed | Isolated clean Compose acceptance migrated to `0005_daily_run_trade_date`; all seven PostgreSQL integration tests, publication/reconciliation, authenticated APIs, and health checks passed. | Reopen if a later migration lacks clean live evidence. |
| R-003 | GitHub Actions and Trivy have not executed remotely. | Closed | Successful Phase 0 main CI completed the sequential job. Trivy retains a HIGH/CRITICAL gate with two third-party-SBOM-only suppressions expiring 2026-09-15; Gitleaks owns secret scanning. | Reopen if CI fails or the suppressions require review. |
| R-004 | Container and frontend builds may pressure the 7.2 GiB host. | Closed | Repeated target-host builds and the complete isolated Phase 1 Compose/browser suite passed; BuildKit reused pinned dependency caches. | Reopen if later image growth causes resource failures. |
| R-005 | Public repository could receive a credential in a future commit. | Managed | Tracked files and reachable history have no high-confidence credential or private-key match; Gitleaks scans full history on `main` pushes. | Review each secret-scan failure and rotate/remove any real credential. |
| R-006 | Authentication/session defects could retain unauthorized access or expose a credential. | Closed | Argon2id hashes only; session and CSRF secrets are opaque server-side hashes. Clean PostgreSQL integration and real-stack Playwright passed login, rotation/refresh, incomplete and unauthenticated download rejection, and logout revocation. Runtime-random E2E credentials are supplied over stdin and never persisted. | Reopen if authentication behavior or exposure changes. |
| R-007 | Concurrent authenticated dashboard requests could deadlock the single async app process. | Closed | Short auth-session mutations are serialized and committed before run/package work; database dependencies commit before response. Concurrent API integration, UI polling, manual use, restart recovery, and real-stack Playwright all kept liveness responsive. | Reopen if app replicas, async database infrastructure, or session-write concurrency changes. |
