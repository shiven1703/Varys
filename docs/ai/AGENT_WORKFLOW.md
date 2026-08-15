# Varys Agent Workflow

## Start an increment

1. Read the documents in `AGENTS.md` order.
2. Inspect `main`, `git status`, and recent commits.
3. Read the current phase acceptance rules and only the contracts/ADRs relevant
   to the increment.
4. Run the smallest relevant baseline check and state any material assumption.

## Implement and verify

- Preserve the locked architecture: one application image for app/worker,
  PostgreSQL-backed dispatch, no broker, no Nginx, and no live NSE in normal
  tests.
- Keep raw artifacts and ready packages immutable; never expose partial or
  unverified downloads.
- Make focused changes, add the smallest useful test, then run the relevant
  check. Do not treat unavailable Docker or CI environments as successful.

## Record and hand off

1. Update `current-state.md`, the current phase file, and risk/dependency
   records whenever facts change.
2. Commit only after the owner accepts the increment.
3. State remaining validation explicitly and wait for owner approval.
4. A phase reaches `USER_APPROVAL_PENDING` only after its full acceptance suite
   passes; only the owner can set `APPROVED`.
