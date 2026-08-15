#!/bin/sh
set -eu

docker compose stop worker

run_id=$(docker compose exec --no-TTY app python -c '
from datetime import UTC, date, datetime, timedelta
from varys.config import load_settings
from varys.db import create_session_factory
from varys.runs import claim_next_run, create_daily_run

settings = load_settings()
with create_session_factory(settings.database_url).begin() as database:
    run = create_daily_run(database, date(2026, 8, 14))
    if run is None:
        raise RuntimeError("restart-recovery run already exists")
    run.created_at = datetime(2000, 1, 1, tzinfo=UTC)
    claimed = claim_next_run(database, "stopped-worker")
    if claimed is None or claimed.id != run.id:
        raise RuntimeError("restart-recovery run was not claimed")
    claimed.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    print(run.id)
')

docker compose restart app
docker compose up --no-build --detach --wait app worker

attempt=0
while [ "$attempt" -lt 30 ]; do
    set +e
    docker compose exec --no-TTY -e "RECOVERY_RUN_ID=$run_id" app python -c '
import os
from uuid import UUID
from sqlalchemy import select
from varys.config import load_settings
from varys.db import create_session_factory
from varys.packages import Package, PackageState
from varys.runs import Run, RunState

settings = load_settings()
with create_session_factory(settings.database_url)() as database:
    run_id = UUID(os.environ["RECOVERY_RUN_ID"])
    run = database.get(Run, run_id)
    package = database.scalar(select(Package).where(Package.run_id == run_id))
    if run is None:
        raise SystemExit(2)
    if run.state in (RunState.FAILED, RunState.CANCELLED):
        raise SystemExit(2)
    if run.state in (RunState.COMPLETED, RunState.COMPLETED_WITH_WARNINGS):
        if package is None or package.state not in (
            PackageState.READY,
            PackageState.READY_WITH_WARNINGS,
        ):
            raise SystemExit(2)
        raise SystemExit(0)
    raise SystemExit(1)
'
    result=$?
    set -e
    case "$result" in
        0)
            printf '%s\n' "Restart recovery completed run $run_id"
            exit 0
            ;;
        1)
            attempt=$((attempt + 1))
            sleep 1
            ;;
        *)
            printf '%s\n' "Restart recovery failed for run $run_id" >&2
            exit "$result"
            ;;
    esac
done

printf '%s\n' "Restart recovery timed out for run $run_id" >&2
exit 1
