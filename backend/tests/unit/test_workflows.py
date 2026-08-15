from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from varys.runs import Run, RunState
from varys.storage import StoragePaths, initialize_storage
from varys.workflows import WorkflowError, execute_daily_fixture_run


def test_fixture_daily_workflow_writes_immutable_raw_workspace_and_ready_archive(
    tmp_path: Path,
) -> None:
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)
    run = _run(date(2026, 8, 14))
    database = MagicMock()

    assert execute_daily_fixture_run(database, paths, run) is True
    assert paths.raw_artifact(_fixture_digest("udiff_bhavcopy.csv")).is_file()
    assert (paths.run_workspace(str(run.id)) / "equity_market_data.csv").is_file()
    assert list((paths.ready_root / "daily").glob("*.zip"))


def test_fixture_daily_workflow_rejects_unavailable_fixture_date(
    tmp_path: Path,
) -> None:
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)

    with pytest.raises(WorkflowError, match="not published"):
        execute_daily_fixture_run(MagicMock(), paths, _run(date(2026, 8, 15)))


def _run(trade_date: date) -> Run:
    now = datetime.now(UTC)
    return Run(
        id=uuid4(),
        kind="daily",
        state=RunState.RUNNING,
        worker_id="test-worker",
        lease_expires_at=now + timedelta(minutes=5),
        heartbeat_at=now,
        requested_action=None,
        trade_date=trade_date,
        created_at=now,
        updated_at=now,
    )


def _fixture_digest(filename: str) -> str:
    from hashlib import sha256

    return sha256(
        (Path(__file__).parents[2] / "varys" / "fixtures" / filename).read_bytes()
    ).hexdigest()
