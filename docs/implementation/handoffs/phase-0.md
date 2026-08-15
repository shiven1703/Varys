# Phase 0 New-Chat Handover Prompt

Copy the text below into a new Codex chat started from the Varys repository
root.

```text
We are starting Varys Phase 0 — Foundation and contract lock.

Do not rely on previous chat memory. Reconstruct all state from the repository.
Pre-Phase was explicitly owner-approved on 2026-08-15. Phase 0 is NOT_STARTED
and is authorized to begin under implementation plan revision 3, but it is not
approved.

The owner-selected Git workflow uses main as the default working branch through
the first V1 release. Create or switch to a temporary branch only when the owner
explicitly requests one for a specific risk, experiment, or review boundary.
Do not push or rewrite Git history without explicit authorization.

First read completely, in this order:
1. AGENTS.md
2. docs/implementation/implementation-plan.md
3. docs/implementation/varys_requirements_and_architecture_spec.md
4. docs/implementation/varys_gpt56_implementation_planning_handoff.md
5. docs/implementation/varys_llm_handover_pre_implementation.md
6. docs/implementation/current-state.md
7. docs/implementation/phases/phase-0.md
8. docs/implementation/phases/pre-phase.md
9. relevant existing files under docs/contracts/
10. relevant existing ADRs under docs/architecture/decisions/
11. docs/implementation/risk-register.md, if present
12. docs/implementation/dependency-baseline.md, if present
13. docs/implementation/definition-of-done.md, if present

Then inspect the actual repository:
- git status --short --branch
- git branch --show-current
- git rev-parse HEAD
- git log -n 10 --oneline
- docker --version
- docker buildx version
- docker compose version
- docker run --rm hello-world
- codex --version

Expected Git state at handover creation:
- branch: main
- commit: aad51c5ef61816df2c53233b8eaa2295a2f97914
- intentional uncommitted bootstrap paths: .codex/, AGENTS.md, and docs/

These bootstrap changes were left uncommitted because staging/commit permission
was not granted in the handover session. Inspect them and do not discard them.
Before application implementation, request permission to stage and commit the
reviewed bootstrap baseline on main. If the actual changes extend beyond these
documented paths, stop and report the discrepancy.

The owner added all three higher-authority planning inputs under
docs/implementation/. Read them completely before contract work. Reconcile
their approved requirements with the implementation plan and explicitly report
any contradiction instead of silently choosing a source or inventing details.

Interpret the two handoff files as historical planning and traceability inputs.
Their old "planning only" and default-branch directions are superseded. Current
execution authority is AGENTS.md, the approved product specification,
implementation plan revision 3, current-state, and this phase state.

The 2026-08-15 alignment audit already resolved these points:
- Use main by default through the first V1 release; use a temporary branch only
  when the owner explicitly requests one for a specific need.
- Preserve every required check, running GitHub Actions on pushes to main.
- Index CSV must include the approved minimum
  volume_or_shares_traded_if_available and turnover_if_available fields; use NA
  when unavailable according to the exact Phase 0 contract.
- JSON APIs live under /api/v1/* and authenticated binary downloads under
  /files/*.
- Phase 0 Iteration 0J must make repository state documents the complete
  progress and acceptance ledger.
- The plan's 0A-0J iterations map to ten approved Phase 0 outcomes; Phase 1's
  1A-1I iterations map to eight approved Phase 1 outcomes.

Before editing, report:
1. verified main-branch baseline and exact commit,
2. whether the working tree matches the documented bootstrap-only changes,
3. current Phase 0 status and approved scope,
4. relevant available authority sources, contracts, and ADRs,
5. exact scope of the first implementation iteration,
6. files/modules expected to change,
7. tests and validation commands to be used,
8. known risks, assumptions, and blockers,
9. anything that conflicts with the implementation plan.

If the branch is not main without an explicit owner instruction, the working
tree contains changes outside the documented bootstrap paths, or repository
evidence contradicts the handover, stop and report the discrepancy.

Implement Phase 0 iteratively, not as one unreviewable change. Start with
Iteration 0A (Contracts) after reconciling the approved source documents. Before
the first implementation edit, update docs/implementation/phases/phase-0.md
from NOT_STARTED to IN_PROGRESS and record the starting commit. Do not begin
Phase 1 functionality.

Iteration 0A is limited to the twelve versioned contract files listed in plan
section 10.2 and their valid examples/review evidence. It must eliminate output
ambiguity needed by the Phase 1 fixture slice, including exact index/universe
columns, Decimal-safe numeric formatting, LF/final-newline rules, deterministic
ordering, run/package states, source-adapter responsibilities, API/download
surfaces, configuration, and safe filesystem paths. Do not scaffold application
code during 0A.

After each meaningful increment:
- run the smallest relevant deterministic checks,
- self-review the diff,
- keep changes scoped,
- update phase evidence and current-state facts,
- record deviations, risks, and dependency decisions,
- keep working on main by default with small coherent checkpoints.

Do not redesign locked architecture, use live NSE in normal tests, weaken tests,
add excluded infrastructure, expose browser-controlled filesystem paths, or
claim owner approval.

When every Phase 0 acceptance criterion passes, set only:
Status: USER_APPROVAL_PENDING
Owner approved: no

Then stop for explicit owner approval. Never set Phase 0 to APPROVED yourself.
```
