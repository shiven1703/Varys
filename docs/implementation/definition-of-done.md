# Definition of Done

## Implementation increment

- Scope matches the current phase acceptance rules.
- Relevant contracts, ADRs, tests, and documentation are updated.
- The smallest relevant checks pass, with unavailable environments recorded.
- `git diff --check` passes and unrelated changes are excluded.
- `current-state.md`, the phase evidence file, risk register, and dependency
  baseline reflect the result.
- Owner acceptance is recorded before the increment is committed.

## Phase completion

- Every planned iteration is implemented and owner-accepted.
- The phase acceptance suite in `docs/implementation/implementation-plan.md`
  passes with exact evidence in the phase file.
- Known risks and deviations are reviewed; no unavailable check is called a
  pass.
- Codex sets `USER_APPROVAL_PENDING`; only the owner may set `APPROVED` and
  permit the next phase.
