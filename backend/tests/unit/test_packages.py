from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

import pytest

from varys.packages import (
    FindingSeverity,
    PackageArtifactInput,
    PackageError,
    PackageIdentity,
    PackageKind,
    PackageProvenance,
    PackageSpecification,
    PreparationFinding,
    inspect_archive,
    stage_package,
    write_preparation_report,
)
from varys.storage import StoragePaths, atomic_publish, initialize_storage

_FIXTURES = Path(__file__).parents[1] / "golden" / "fixtures"
_PREPARED_AT = datetime(2026, 8, 14, 18, 30, tzinfo=UTC)


def test_staged_archive_is_deterministic_verified_and_has_no_part_members(
    tmp_path: Path,
) -> None:
    specification = _daily_specification(UUID("00000000-0000-4000-8000-000000000001"))
    first_paths = _storage_paths(tmp_path / "first")
    second_paths = _storage_paths(tmp_path / "second")

    first = stage_package(first_paths, specification)
    second = stage_package(second_paths, specification)

    assert first.path.read_bytes() == second.path.read_bytes()
    assert [artifact.name for artifact in first.artifacts] == [
        "equity_market_data.csv",
        "index_ohlc.csv",
        "preparation_report.csv",
    ]
    with ZipFile(first.path) as archive:
        assert all(not name.endswith(".part") for name in archive.namelist())
        assert archive.namelist() == sorted(archive.namelist())

    ready_path = first_paths.ready_package("daily", str(specification.identity.id))
    atomic_publish(first.path, ready_path)
    inspected = inspect_archive(ready_path, specification.identity)
    assert inspected.artifacts == first.artifacts
    assert ready_path.exists()


def test_package_rejects_duplicate_business_keys_and_unknown_csv_schema(
    tmp_path: Path,
) -> None:
    equity = (_FIXTURES / "equity.csv").read_bytes()
    duplicate_equity = equity + equity.splitlines(keepends=True)[1]
    paths = _storage_paths(tmp_path)

    with pytest.raises(PackageError, match="duplicate business keys"):
        stage_package(
            paths,
            _daily_specification(
                UUID("00000000-0000-4000-8000-000000000002"), duplicate_equity
            ),
        )

    with pytest.raises(PackageError, match="schema is not recognised"):
        stage_package(
            paths,
            _daily_specification(
                UUID("00000000-0000-4000-8000-000000000003"), b"unknown\nvalue\n"
            ),
        )


def test_preparation_report_is_sorted_and_preserves_literal_na() -> None:
    report = write_preparation_report(
        (
            PreparationFinding(
                FindingSeverity.INFO, "COMPLETE", "PACKAGE", "NA", "complete"
            ),
            PreparationFinding(
                FindingSeverity.WARNING,
                "INDEX_VOLUME_UNAVAILABLE",
                "INDEX_ROW",
                "2026-08-14:NIFTY 50",
                "Verified source did not provide volume",
            ),
        )
    )

    assert report.splitlines()[1].startswith(b"WARNING,INDEX_VOLUME_UNAVAILABLE")
    assert b'INFO,COMPLETE,PACKAGE,"NA",complete' in report


def _daily_specification(
    package_id: UUID, equity_content: bytes | None = None
) -> PackageSpecification:
    return PackageSpecification(
        identity=PackageIdentity(package_id, PackageKind.DAILY, 1),
        prepared_at=_PREPARED_AT,
        provenance=PackageProvenance(
            configuration_fingerprint="a" * 64,
            raw_source_sha256=("b" * 64, "c" * 64),
            source_format_versions=(
                "capital-market-bhavcopy-udiff-v1",
                "nifty-indices-report-v1",
            ),
        ),
        artifacts=(
            PackageArtifactInput(
                "equity_market_data.csv",
                equity_content or (_FIXTURES / "equity.csv").read_bytes(),
            ),
            PackageArtifactInput(
                "index_ohlc.csv", (_FIXTURES / "index.csv").read_bytes()
            ),
        ),
        findings=(
            PreparationFinding(
                FindingSeverity.WARNING,
                "INDEX_VOLUME_UNAVAILABLE",
                "INDEX_ROW",
                "2026-08-14:NIFTY 50",
                "Verified source did not provide volume",
            ),
        ),
    )


def _storage_paths(root: Path) -> StoragePaths:
    paths = StoragePaths.from_root(root)
    initialize_storage(paths)
    return paths
