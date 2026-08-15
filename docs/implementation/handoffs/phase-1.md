# Phase 1 New-Chat Handover Prompt

Copy the text below into a new Codex chat started from the Varys repository
root **only after the owner explicitly approves Phase 0**.

```text
We are preparing to start Varys Phase 1 — fixture-based daily vertical slice.

Do not rely on previous chat memory. Reconstruct state from the repository and
do not begin implementation unless Phase 0 is explicitly owner-approved. At
handover creation, Phase 0 implementation iterations are complete but Phase 0
acceptance evidence is still pending Docker, browser, scanner,
clean-PostgreSQL, and remote-CI execution. If current state is not Phase 0
APPROVED, stop and report the blocker; do not change phase status yourself.

First read, in order:
1. AGENTS.md
2. docs/ai/START_HERE.md
3. docs/ai/AGENT_WORKFLOW.md
4. docs/implementation/implementation-plan.md
5. docs/implementation/varys_requirements_and_architecture_spec.md
6. docs/implementation/varys_gpt56_implementation_planning_handoff.md
7. docs/implementation/varys_llm_handover_pre_implementation.md
8. docs/implementation/current-state.md
9. docs/implementation/phases/phase-0.md
10. docs/implementation/risk-register.md
11. docs/implementation/dependency-baseline.md
12. docs/implementation/definition-of-done.md
13. all relevant `v1` contracts under docs/contracts/
14. ADR-001 and ADR-002 under docs/architecture/decisions/

Then inspect the repository with:
- git status --short --branch
- git branch --show-current
- git rev-parse HEAD
- git log -n 10 --oneline
- make check

Use `main` by default. Do not create a temporary branch, push, rewrite history,
or claim owner approval without explicit owner instruction.

Phase 1 proves a real fixture-only login-to-download slice. It must never call
live NSE in normal tests, add excluded infrastructure, perform long work in a
FastAPI handler, expose browser-selected filesystem paths, or weaken immutable
raw/ready publication rules. Preserve the shared app/worker image and
PostgreSQL-backed run claiming.

Start only Iteration 1A after verifying Phase 0 approval. Its scope is users
and auth-session persistence, Argon2id hashing, `varys create-admin`, login,
logout, current-user endpoint, server-side sessions, secure cookie flags,
timeouts, CSRF, protection, and revocation. Read the API, configuration,
filesystem, run-state, and package-state contracts before editing. Do not start
1B run claiming, adapters, parsers, packages, daily UI, or Phase 1 E2E work in
the same increment.

Before editing, report the verified baseline, Phase 0 approval, exact 1A scope,
relevant contracts/ADRs, expected files, tests, risks, and discrepancies. After
each increment, run focused checks, update current-state/phase/risk/dependency
evidence, and wait for owner acceptance before committing. Only the owner may
approve Phase 1 after its full acceptance suite passes.
```
