"""Fixture-only daily workflow composed for the Phase 1 vertical slice."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from varys.packages import (
    FindingSeverity,
    PackageArtifactInput,
    PackageIdentity,
    PackageKind,
    PackageProvenance,
    PackageSpecification,
    PreparationFinding,
    create_package,
    publish_package,
    write_generated_csv,
)
from varys.parsers import (
    parse_capital_market_bhavcopy,
    parse_index_report,
    parse_nifty500_universe,
    write_equity_csv,
    write_index_csv,
)
from varys.runs import Run
from varys.sources import (
    CapitalMarketBhavcopySource,
    FixtureSourceAdapter,
    IndexReportSource,
    Nifty500UniverseSource,
    SourceClassification,
    SourceReference,
    VerifiedSourceFile,
)
from varys.storage import StoragePaths, atomic_publish, sha256_file, write_durable_bytes


class WorkflowError(ValueError):
    """A fixture daily run cannot produce a verified package."""


def execute_daily_fixture_run(database: Session, paths: StoragePaths, run: Run) -> bool:
    """Build one daily package inside the dedicated worker process.

    Raw source bytes and generated canonical CSVs are persisted before the
    package publisher stages and verifies the immutable archive.
    """
    if run.kind != "daily" or run.trade_date is None:
        raise WorkflowError("fixture workflow requires a dated daily run")
    workspace = paths.run_workspace(str(run.id))
    if not workspace.exists():
        paths.create_run_workspace(str(run.id))

    equity_reference, equity_content = _source_content(
        CapitalMarketBhavcopySource(_fixture_map("udiff_bhavcopy.csv")), run.trade_date
    )
    index_reference, index_content = _source_content(
        IndexReportSource(_fixture_map("index_report.csv")), run.trade_date
    )
    universe_reference, universe_content = _source_content(
        Nifty500UniverseSource(_fixture_map("universe_report.csv")), run.trade_date
    )
    verified_sources = (
        _persist_raw(paths, equity_reference, equity_content),
        _persist_raw(paths, index_reference, index_content),
        _persist_raw(paths, universe_reference, universe_content),
    )
    artifacts = (
        PackageArtifactInput(
            "equity_market_data.csv",
            _write_workspace_csv(
                paths,
                run,
                "equity_market_data.csv",
                write_equity_csv(
                    parse_capital_market_bhavcopy(equity_content, equity_reference)
                ),
            ),
        ),
        PackageArtifactInput(
            "index_ohlc.csv",
            _write_workspace_csv(
                paths,
                run,
                "index_ohlc.csv",
                write_index_csv(parse_index_report(index_content, index_reference)),
            ),
        ),
    )
    # The universe fixture is parsed here to keep source schema verification in
    # the daily vertical slice; daily archives intentionally omit universe.csv.
    parse_nifty500_universe(universe_content, universe_reference)
    identity = PackageIdentity(uuid4(), PackageKind.DAILY, 1)
    package = create_package(database, run.id, identity)
    specification = PackageSpecification(
        identity=identity,
        prepared_at=datetime.now(UTC).replace(microsecond=0),
        provenance=PackageProvenance(
            configuration_fingerprint=_configuration_fingerprint(),
            raw_source_sha256=tuple(source.sha256 for source in verified_sources),
            source_format_versions=tuple(
                source.source_format_version for source in verified_sources
            ),
        ),
        artifacts=artifacts,
        findings=(
            PreparationFinding(
                FindingSeverity.INFO,
                "COMPLETE",
                "PACKAGE",
                str(identity.id),
                "Fixture package complete",
            ),
        ),
    )
    return publish_package(database, paths, package, specification) is not None


def _fixture_map(filename: str) -> dict[date, bytes]:
    content = (Path(__file__).with_name("fixtures") / filename).read_bytes()
    return {date(2026, 8, 14): content}


def _source_content(
    adapter: FixtureSourceAdapter, trade_date: date
) -> tuple[SourceReference, bytes]:
    reference = adapter.discover(trade_date)
    if reference is None:
        raise WorkflowError("fixture source is not published for the requested date")
    response = adapter.download(reference)
    if adapter.classify(response) != SourceClassification.VALID_FILE:
        raise WorkflowError("fixture source is not valid")
    assert response.content is not None
    return reference, response.content


def _persist_raw(
    paths: StoragePaths, reference: SourceReference, content: bytes
) -> VerifiedSourceFile:
    digest = sha256(content).hexdigest()
    destination = paths.raw_artifact(digest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != digest:
            raise WorkflowError("immutable raw artifact digest does not match")
    else:
        part_path = write_durable_bytes(destination, content)
        atomic_publish(part_path, destination)
    return VerifiedSourceFile(
        sha256=digest,
        original_filename=reference.filename,
        size_bytes=len(content),
        source_report=reference.source_report,
        source_format_version=reference.source_format_version,
    )


def _write_workspace_csv(
    paths: StoragePaths, run: Run, name: str, content: bytes
) -> bytes:
    destination = paths.run_workspace(str(run.id)) / name
    if destination.exists():
        if destination.read_bytes() != content:
            raise WorkflowError("existing generated CSV differs from canonical output")
        return content
    write_generated_csv(paths, str(run.id), name, content)
    return content


def _configuration_fingerprint() -> str:
    payload = json.dumps(
        {"source_mode": "fixture", "workflow": "daily-v1"},
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode()).hexdigest()
