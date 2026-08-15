import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from varys.db import create_session_factory, upgrade_database
from varys.packages import (
    FindingSeverity,
    Package,
    PackageArtifactInput,
    PackageIdentity,
    PackageKind,
    PackageProvenance,
    PackageSpecification,
    PackageState,
    PreparationFinding,
    create_package,
    publish_package,
    reconcile_packages,
    stage_package,
)
from varys.runs import create_run
from varys.storage import StoragePaths, atomic_publish, initialize_storage

_FIXTURES = Path(__file__).parents[1] / "golden" / "fixtures"


@pytest.mark.integration
def test_package_readiness_follows_final_archive_and_reconciles_after_rename(
    tmp_path: Path,
) -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    upgrade_database(database_url)
    factory = create_session_factory(database_url)
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)

    ready_identity = PackageIdentity(
        UUID("00000000-0000-4000-8000-000000000101"), PackageKind.DAILY, 1
    )
    with factory.begin() as database:
        run = create_run(database, "daily")
        package = create_package(database, run.id, ready_identity)
        published = publish_package(
            database, paths, package, _specification(ready_identity)
        )
        assert published is not None
        assert package.state == PackageState.READY_WITH_WARNINGS
        assert (paths.root / published.relative_path).is_file()

    adopted_identity = PackageIdentity(
        UUID("00000000-0000-4000-8000-000000000102"), PackageKind.DAILY, 2
    )
    with factory.begin() as database:
        run = create_run(database, "daily")
        create_package(database, run.id, adopted_identity)
    staged = stage_package(paths, _specification(adopted_identity))
    atomic_publish(
        staged.path,
        paths.ready_package(adopted_identity.kind, str(adopted_identity.id)),
    )

    with factory.begin() as database:
        result = reconcile_packages(database, paths)
        adopted = database.get(Package, adopted_identity.id)
        assert result.adopted == 1
        assert adopted is not None
        assert adopted.state == PackageState.READY_WITH_WARNINGS
        assert adopted.relative_path is not None
        assert (paths.root / adopted.relative_path).is_file()


def _specification(identity: PackageIdentity) -> PackageSpecification:
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
            PackageArtifactInput(
                "equity_market_data.csv", (_FIXTURES / "equity.csv").read_bytes()
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
