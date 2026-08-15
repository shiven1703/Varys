# Dependency Baseline

Status: Phase 0 Iteration 0C. Update this document with each dependency or
toolchain change.

## Host prerequisites

| Tool | Verified version | Purpose |
| --- | --- | --- |
| Python | 3.12.3 | Creates the repository-local virtual environment. |
| pip | 24.0 | Installs pinned project tooling into `.venv`. |
| GNU Make | 4.3 | Stable developer command interface. |
| Git | 2.43.0 | Source control. |
| ripgrep | 14.1.0 | Repository search. |

`uv` is not a host prerequisite. `make bootstrap` creates `.venv` and installs
the exact pins in `requirements-dev.lock` there, so check commands use no global
Python packages. It retains the venv-provided pip and does not upgrade it.

## Pinned development dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| setuptools | 75.8.0 | Editable project installation backend. |
| mypy | 1.15.0 | Static type checks. |
| pytest | 8.3.5 | Python test runner. |
| ruff | 0.9.10 | Formatting and linting. |

Runtime dependencies are intentionally absent until Iteration 0D establishes
the FastAPI and worker bootstrap. The project requires Python `>=3.12,<3.13`.
