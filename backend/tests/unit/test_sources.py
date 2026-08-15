from datetime import date
from pathlib import Path

import pytest

from varys.sources import (
    CapitalMarketBhavcopySource,
    FixtureResponse,
    IndexReportSource,
    Nifty500UniverseSource,
    SourceAdapter,
    SourceClassification,
)
from varys.storage import StoragePaths, initialize_storage


@pytest.mark.parametrize(
    "adapter",
    [
        Nifty500UniverseSource({date(2026, 8, 14): b"universe fixture"}),
        CapitalMarketBhavcopySource({date(2026, 8, 14): b"bhavcopy fixture"}),
        IndexReportSource({date(2026, 8, 14): b"index fixture"}),
    ],
)
def test_fixture_adapters_follow_the_source_contract(adapter: SourceAdapter) -> None:
    trade_date = date(2026, 8, 14)

    reference = adapter.discover(trade_date)

    assert reference is not None
    response = adapter.download(reference)
    assert adapter.classify(response) == SourceClassification.VALID_FILE
    verified = adapter.verify(response)
    assert verified.original_filename == reference.filename
    assert verified.source_report == reference.source_report
    assert verified.size_bytes == len(response.content or b"")
    assert len(verified.sha256) == 64
    assert adapter.discover(date(2026, 8, 15)) is None


def test_fixture_adapter_classifies_missing_and_empty_content() -> None:
    adapter = IndexReportSource({})
    reference = IndexReportSource({date(2026, 8, 14): b"source"}).discover(
        date(2026, 8, 14)
    )

    assert reference is not None
    assert (
        adapter.classify(FixtureResponse(reference, None))
        == SourceClassification.NOT_FOUND
    )
    assert (
        adapter.classify(FixtureResponse(reference, b""))
        == SourceClassification.INVALID_CONTENT
    )
    with pytest.raises(ValueError, match="not a valid"):
        adapter.verify(FixtureResponse(reference, b""))


def test_run_workspaces_are_isolated_and_created_once(tmp_path: Path) -> None:
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)

    workspace = paths.create_run_workspace("123e4567-e89b-12d3-a456-426614174000")

    assert workspace.is_dir()
    assert workspace.parent == paths.work_root
    with pytest.raises(FileExistsError):
        paths.create_run_workspace("123e4567-e89b-12d3-a456-426614174000")
