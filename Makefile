PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_RUFF := $(VENV)/bin/ruff
VENV_MYPY := $(VENV)/bin/mypy
VENV_PYTEST := $(VENV)/bin/pytest
BACKEND_PYTHONPATH := PYTHONPATH=backend

.DEFAULT_GOAL := check
.PHONY: bootstrap format lint typecheck test test-unit test-integration test-golden test-failure-injection test-e2e build compose-up compose-down compose-smoke check

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --requirement requirements-dev.lock

format:
	$(VENV_RUFF) check --fix backend
	$(VENV_RUFF) format backend

lint:
	$(VENV_RUFF) check backend

typecheck:
	$(BACKEND_PYTHONPATH) $(VENV_MYPY)

test: test-unit

test-unit:
	$(BACKEND_PYTHONPATH) $(VENV_PYTEST) backend/tests/unit

test-integration:
	$(BACKEND_PYTHONPATH) $(VENV_PYTEST) -m integration backend/tests/integration

test-golden:
	$(BACKEND_PYTHONPATH) $(VENV_PYTEST) backend/tests/golden

test-failure-injection:
	$(BACKEND_PYTHONPATH) $(VENV_PYTEST) backend/tests/failure_injection

test-e2e:
	npm --prefix frontend run test:e2e

build:
	docker compose build

compose-up:
	docker compose up -d

compose-down:
	docker compose down

compose-smoke:
	sh scripts/ci/compose-smoke.sh

check: lint typecheck test-unit
