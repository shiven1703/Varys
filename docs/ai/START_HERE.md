# Varys Agent Start Here

Read `AGENTS.md` first, then follow its ordered document list. The current
implementation ledger is `docs/implementation/current-state.md`; the current
phase evidence is `docs/implementation/phases/phase-0.md`.

## Current boundary

Phase 0 is `IN_PROGRESS` in Iteration 0J. Do not begin Phase 1. Only the owner
can approve a phase: Codex records evidence and may set
`USER_APPROVAL_PENDING`, but never `APPROVED`.

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
