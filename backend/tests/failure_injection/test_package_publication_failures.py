from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest

from varys.packages import (
    PackageArtifactInput,
    PackageError,
    PackageIdentity,
    PackageKind,
    PackageProvenance,
    PackageSpecification,
    stage_package,
    write_generated_csv,
)
from varys.storage import StoragePaths, initialize_storage

_FIXTURES = Path(__file__).parents[1] / "golden" / "fixtures"
_EQUITY = (_FIXTURES / "equity.csv").read_bytes()
_INDEX = (_FIXTURES / "index.csv").read_bytes()


def test_generated_csv_write_and_post_verify_failures_leave_no_completed_csv(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    first_run = "00000000-0000-4000-8000-000000000201"
    first_workspace = paths.create_run_workspace(first_run)

    with patch("varys.storage.os.fsync", side_effect=OSError("disk failure")):
        with pytest.raises(OSError, match="disk failure"):
            write_generated_csv(paths, first_run, "equity_market_data.csv", _EQUITY)

    assert not (first_workspace / "equity_market_data.csv").exists()
    assert (first_workspace / "equity_market_data.csv.part").exists()

    second_run = "00000000-0000-4000-8000-000000000202"
    second_workspace = paths.create_run_workspace(second_run)
    with patch("varys.packages.atomic_publish", side_effect=OSError("rename failure")):
        with pytest.raises(OSError, match="rename failure"):
            write_generated_csv(paths, second_run, "equity_market_data.csv", _EQUITY)

    assert not (second_workspace / "equity_market_data.csv").exists()
    assert (second_workspace / "equity_market_data.csv.part").exists()


def test_zip_and_post_archive_verification_failures_leave_no_ready_package(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    identity = PackageIdentity(
        UUID("00000000-0000-4000-8000-000000000203"), PackageKind.DAILY, 1
    )
    with patch("varys.packages._build_zip_archive", side_effect=OSError("zip failure")):
        with pytest.raises(OSError, match="zip failure"):
            stage_package(paths, _specification(identity))

    assert not paths.staging_package(str(identity.id)).exists()
    assert not paths.ready_package(identity.kind, str(identity.id)).exists()

    with patch(
        "varys.packages.inspect_archive", side_effect=PackageError("verify failure")
    ):
        with pytest.raises(PackageError, match="verify failure"):
            stage_package(paths, _specification(identity))

    assert paths.staging_package(str(identity.id)).exists()
    assert not paths.ready_package(identity.kind, str(identity.id)).exists()
    replacement = PackageIdentity(
        UUID("00000000-0000-4000-8000-000000000204"), PackageKind.DAILY, 2
    )
    assert stage_package(paths, _specification(replacement)).path.exists()


def _specification(identity: PackageIdentity) -> PackageSpecification:
    from datetime import UTC, datetime

    return PackageSpecification(
        identity=identity,
        prepared_at=datetime(2026, 8, 14, 18, 30, tzinfo=UTC),
        provenance=PackageProvenance(
            configuration_fingerprint="a" * 64,
            raw_source_sha256=("b" * 64, "c" * 64),
            source_format_versions=(
                "capital-market-bhavcopy-udiff-v1",
                "nifty-indices-report-v1",
            ),
        ),
        artifacts=(
            PackageArtifactInput("equity_market_data.csv", _EQUITY),
            PackageArtifactInput("index_ohlc.csv", _INDEX),
        ),
        findings=(),
    )


def _paths(root: Path) -> StoragePaths:
    paths = StoragePaths.from_root(root / "data")
    initialize_storage(paths)
    return paths
