# Varys Agent Start Here

Read `AGENTS.md` first, then follow its ordered document list. The current
implementation ledger is `docs/implementation/current-state.md`; the current
phase evidence is `docs/implementation/phases/phase-1.md`.

## Current boundary

Phase 1 is `IN_PROGRESS`. Iterations 1A through 1H are owner-accepted;
Iteration 1I implementation and local acceptance are complete, with owner
acceptance and full GitHub Actions evidence pending. Phase 0 was owner-approved
on 2026-08-15. Only the owner can approve a phase: Codex records evidence and
may set `USER_APPROVAL_PENDING`, but never `APPROVED`.

## Commands

Start with `make check`. Run `make test-golden` and
`make test-failure-injection` for their dedicated layers. PostgreSQL integration
requires `VARYS_TEST_DATABASE_URL`; Docker-backed commands require a Docker
daemon and `.env` copied from `.env.example`. Frontend commands are documented
in `README.md`.

## Evidence

After each scoped increment, update `current-state.md` and the current phase
file with the commands run, results, limitations, and next action. Consult
`risk-register.md`, `dependency-baseline.md`, and `definition-of-done.md`
before declaring an increment ready for owner review.
