# Pre-Phase State

Status: APPROVED
Owner approved: yes
Plan revision: 1
Started from commit: `aad51c5ef61816df2c53233b8eaa2295a2f97914`
Current commit: Resolve the approved handover commit with `git rev-parse HEAD`

## Objective

Provide a predictable Ubuntu, Codex, Git, Docker, and repository baseline from
which Phase 0 can start reproducibly.

## Scope

- Verify the host baseline and required CLI tools.
- Install Docker Engine, Buildx, and Compose from Docker's official Ubuntu
  repository.
- Configure safe Git and Codex defaults.
- Establish repository instructions and factual state ledgers.
- Place the implementation plan at its authoritative repository path.
- Record reproducible acceptance evidence.

## Out of scope

- Phase 0 contracts, architecture documents, application scaffolding, database,
  frontend, runtime topology, tests, and CI.
- Any Varys market-data product functionality.
- Any claim of owner approval.

## Implementation iterations

- Iteration 1: host inspection and required CLI verification.
- Iteration 2: Docker official-repository installation and daemon smoke test.
- Iteration 3: Git/Codex settings and repository governance bootstrap.
- Iteration 4: acceptance verification and evidence review.

## Acceptance criteria

The authoritative criteria are in section P.10 of
`docs/implementation/implementation-plan.md`.

## Acceptance evidence

Acceptance date: 2026-08-15

```text
PRE_PHASE_ACCEPTANCE = PASSED
PRE_PHASE_STATUS = APPROVED
```

Host baseline:

- Ubuntu 24.04.4 LTS, x86_64, kernel 7.0.0-28-generic.
- Root filesystem: 197 GiB total, 95 GiB available at verification.
- Memory: 7.2 GiB total, 2.6 GiB available at verification.

Tool checks:

| Command | Result |
| --- | --- |
| `git --version` | PASS — 2.43.0 |
| `curl --version` | PASS — 8.5.0 |
| `jq --version` | PASS — 1.7 |
| `rg --version` | PASS — 14.1.0 |
| `docker --version` | PASS — 29.7.2 |
| `docker buildx version` | PASS — 0.36.1 |
| `docker compose version` | PASS — 5.4.0 |
| `codex --version` | PASS — 0.146.0-alpha.9.2 |
| `codex --strict-config --version` | PASS — project config parsed without a strict-config error |
| `docker run --rm hello-world` | PASS — image ran successfully |

Docker evidence:

- Packages came from Docker's official Ubuntu `noble/stable` apt repository.
- Docker client/server negotiation passed at version 29.7.2.
- Buildx and Compose plugins responded successfully.
- The Docker daemon completed `hello-world` as root immediately after install.
- A fresh login context for user `shivam` completed `hello-world` using Docker
  group membership, proving non-root daemon access for future sessions.

Repository evidence:

- Acceptance ran on `phase/pre-bootstrap`; the unchanged bootstrap working tree
  was then switched to `main`, which is the owner's default branch through the
  first V1 release.
- Starting commit: `aad51c5ef61816df2c53233b8eaa2295a2f97914`.
- Git identity is configured; new-repository default is `main`; pulls are
  fast-forward-only.
- `AGENTS.md`, `.codex/config.toml`, the relocated 2,402-line implementation
  plan, `current-state.md`, and this phase state file are present.
- The current Codex session started at the repository root and read the complete
  implementation plan.
- Codex created, validated, and removed a harmless workspace probe file.
- `git diff --check` passed.
- Before approval, `git status` contained only the intentional Pre-Phase
  bootstrap files under `.codex/`, `AGENTS.md`, and `docs/`.
- The owner explicitly approved Pre-Phase on 2026-08-15.

## Deviations from plan

- The plan's initial `docker run --rm hello-world` wording was verified both as
  root during installation and as user `shivam` in a fresh login context. The
  already-running Codex process cannot inherit new supplementary groups; the
  next login/session will inherit Docker access normally.
- The owner selected `main` as the default working branch through the first V1
  release because this is a single-developer project. A temporary branch is
  used only when the owner explicitly requests one for a specific need.

## Known limitations

- Docker-group membership becomes available to normal commands after the next
  user login/session.
- A stale non-project VS Code environment line in `/home/shivam/.profile` emits
  a harmless warning. It is documented rather than silently changing personal
  shell configuration.

## Risks opened/closed

- Closed: Docker subcommands and non-root daemon access passed in a fresh login
  context after group membership was refreshed.
- Closed: Docker was initially absent; the official stable packages are now
  installed and the daemon completed the `hello-world` smoke test.

## Decisions/ADRs created

None. Phase 0 owns the initial architecture ADRs.

## Next actions

- Commit the approved bootstrap and Phase 0 handover on `main`.
- Start Phase 0 in a new Codex chat using the repository handover prompt.

## Owner approval

Approved by the owner on 2026-08-15 through the explicit instruction:
`approved`.
