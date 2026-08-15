#!/bin/sh
set -eu

cleanup() {
    docker compose down --volumes --remove-orphans
}

trap cleanup EXIT
docker compose up --build --detach --wait
docker compose ps
docker compose exec --no-TTY app python -m pytest -m integration backend/tests/integration
docker compose exec --no-TTY app python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/health/live')"
docker compose exec --no-TTY app python -c "from urllib.request import urlopen; assert b'app-root' in urlopen('http://127.0.0.1:8000/').read()"
