PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_RUFF := $(VENV)/bin/ruff
VENV_MYPY := $(VENV)/bin/mypy
VENV_PYTEST := $(VENV)/bin/pytest

.DEFAULT_GOAL := check
.PHONY: bootstrap format lint typecheck test test-unit test-integration test-golden test-e2e build compose-up compose-down compose-smoke check

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --requirement requirements-dev.lock

format:
	$(VENV_RUFF) format backend

lint:
	$(VENV_RUFF) check backend

typecheck:
	$(VENV_MYPY)

test: test-unit

test-unit:
	$(VENV_PYTEST) backend/tests/unit

test-integration:
	@echo "Integration tests are introduced in Iteration 0E."

test-golden:
	@echo "Golden tests are introduced in Iteration 0I."

test-e2e:
	@echo "Browser E2E tests are introduced in Iteration 0I."

build:
	@echo "Application image build is introduced in Iteration 0H."

compose-up:
	@echo "Compose topology is introduced in Iteration 0H."

compose-down:
	@echo "Compose topology is introduced in Iteration 0H."

compose-smoke:
	@echo "Compose smoke testing is introduced in Iteration 0H."

check: lint typecheck test-unit
