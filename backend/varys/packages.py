"""Deterministic, recoverable package publication for Phase 1 fixtures."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    delete,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from varys.auth import Base
from varys.parsers import EQUITY_SCHEMA, INDEX_SCHEMA, UNIVERSE_SCHEMA
from varys.storage import (
    StoragePaths,
    atomic_publish,
    sha256_file,
    write_durable_bytes,
    write_durable_part,
)

_DIGEST = re.compile(r"[0-9a-f]{64}")
_FINDING_CODE = re.compile(r"[A-Z][A-Z0-9_]*")
_PACKAGE_KINDS = frozenset({"daily", "universe", "backfill"})
_READY_STATES = frozenset({"READY", "READY_WITH_WARNINGS"})
_FINDING_SUBJECTS = frozenset(
    {"PACKAGE", "SOURCE_FILE", "EQUITY_ROW", "INDEX_ROW", "UNIVERSE_ROW"}
)
_PREPARATION_HEADER = ("severity", "code", "subject_type", "subject_id", "message")


class PackageKind(StrEnum):
    DAILY = "daily"
    UNIVERSE = "universe"
    BACKFILL = "backfill"


class PackageState(StrEnum):
    BUILDING = "BUILDING"
    VERIFYING = "VERIFYING"
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    SUPERSEDED = "SUPERSEDED"


class FindingSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PackageError(ValueError):
    """Package input or archive verification failed."""


@dataclass(frozen=True, slots=True)
class PackageIdentity:
    id: UUID
    kind: PackageKind
    version: int


@dataclass(frozen=True, slots=True)
class PackageArtifactInput:
    name: str
    content: bytes


@dataclass(frozen=True, slots=True)
class PackageArtifact:
    name: str
    sha256: str
    size_bytes: int
    row_count: int | None


@dataclass(frozen=True, slots=True)
class PreparationFinding:
    severity: FindingSeverity
    code: str
    subject_type: str
    subject_id: str
    message: str


@dataclass(frozen=True, slots=True)
class PackageProvenance:
    configuration_fingerprint: str
    raw_source_sha256: tuple[str, ...]
    source_format_versions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PackageSpecification:
    identity: PackageIdentity
    prepared_at: datetime
    provenance: PackageProvenance
    artifacts: tuple[PackageArtifactInput, ...]
    findings: tuple[PreparationFinding, ...]


@dataclass(frozen=True, slots=True)
class PublishedArchive:
    relative_path: str
    sha256: str
    size_bytes: int
    artifacts: tuple[PackageArtifact, ...]
    state: PackageState


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    adopted: int
    quarantined: int
    staged_parts: int


@dataclass(frozen=True, slots=True)
class StagedArchive:
    path: Path
    artifacts: tuple[PackageArtifact, ...]
    state: PackageState


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer())
    state: Mapped[str] = mapped_column(String(32))
    relative_path: Mapped[str | None] = mapped_column(String(256))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger())
    sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PackageFile(Base):
    __tablename__ = "package_files"

    package_id: Mapped[UUID] = mapped_column(
        ForeignKey("packages.id"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger())
    row_count: Mapped[int | None] = mapped_column(Integer())


def create_package(
    database: Session, run_id: UUID, identity: PackageIdentity
) -> Package:
    if identity.version < 1:
        raise PackageError("package version must be positive")
    now = _now()
    package = Package(
        id=identity.id,
        run_id=run_id,
        kind=identity.kind,
        version=identity.version,
        state=PackageState.BUILDING,
        relative_path=None,
        size_bytes=None,
        sha256=None,
        created_at=now,
        updated_at=now,
    )
    database.add(package)
    return package


def publish_package(
    database: Session,
    paths: StoragePaths,
    package: Package,
    specification: PackageSpecification,
) -> PublishedArchive | None:
    """Publish only after archive verification; caller owns the DB transaction."""
    _validate_package_record(package, specification.identity)
    if any(
        finding.severity == FindingSeverity.ERROR for finding in specification.findings
    ):
        package.state = PackageState.FAILED
        package.updated_at = _now()
        return None

    package.state = PackageState.VERIFYING
    package.updated_at = _now()
    staged = stage_package(paths, specification)

    ready_path = paths.ready_package(
        specification.identity.kind, str(specification.identity.id)
    )
    atomic_publish(staged.path, ready_path)
    published = PublishedArchive(
        relative_path=str(ready_path.relative_to(paths.root)),
        sha256=sha256_file(ready_path),
        size_bytes=ready_path.stat().st_size,
        artifacts=staged.artifacts,
        state=staged.state,
    )
    _record_ready_package(database, package, published)
    return published


def stage_package(
    paths: StoragePaths, specification: PackageSpecification
) -> StagedArchive:
    """Build and verify a deterministic archive in the non-downloadable staging root."""
    if any(
        finding.severity == FindingSeverity.ERROR for finding in specification.findings
    ):
        raise PackageError("package has blocking preparation findings")
    archive_bytes, artifacts = _build_archive(specification)
    staging_path = paths.staging_package(str(specification.identity.id))
    write_durable_part(staging_path, archive_bytes)
    inspected = inspect_archive(staging_path, specification.identity)
    if inspected.artifacts != artifacts:
        raise PackageError("archive artifact metadata differs from generated metadata")
    return StagedArchive(staging_path, inspected.artifacts, inspected.state)


def write_generated_csv(
    paths: StoragePaths, run_id: str, name: str, content: bytes
) -> Path:
    """Durably verify a canonical CSV in its isolated, non-downloadable workspace."""
    _csv_row_count(name, content)
    workspace = paths.run_workspace(run_id)
    if not workspace.is_dir():
        raise PackageError("run workspace does not exist")
    destination = paths.resolve_under(workspace, name)
    part_path = write_durable_bytes(destination, content)
    _csv_row_count(name, part_path.read_bytes())
    atomic_publish(part_path, destination)
    return destination


def reconcile_packages(database: Session, paths: StoragePaths) -> ReconciliationResult:
    """Adopt post-rename BUILDING archives and quarantine corrupt ready records."""
    adopted = 0
    quarantined = 0
    building = database.scalars(
        select(Package).where(
            Package.state.in_((PackageState.BUILDING, PackageState.VERIFYING))
        )
    )
    for package in building:
        ready_path = paths.ready_package(package.kind, str(package.id))
        if not ready_path.is_file():
            continue
        try:
            inspected = inspect_archive(
                ready_path,
                PackageIdentity(package.id, PackageKind(package.kind), package.version),
            )
        except (OSError, PackageError, zipfile.BadZipFile):
            package.state = PackageState.QUARANTINED
            package.updated_at = _now()
            quarantined += 1
            continue
        _record_ready_package(
            database,
            package,
            PublishedArchive(
                relative_path=str(ready_path.relative_to(paths.root)),
                sha256=sha256_file(ready_path),
                size_bytes=ready_path.stat().st_size,
                artifacts=inspected.artifacts,
                state=inspected.state,
            ),
        )
        adopted += 1

    ready = database.scalars(select(Package).where(Package.state.in_(_READY_STATES)))
    for package in ready:
        try:
            ready_path = _ready_path_from_record(paths, package)
            inspected = inspect_archive(
                ready_path,
                PackageIdentity(package.id, PackageKind(package.kind), package.version),
            )
            if (
                package.size_bytes != ready_path.stat().st_size
                or package.sha256 != sha256_file(ready_path)
                or package.state != inspected.state
            ):
                raise PackageError("ready package metadata is inconsistent")
        except (OSError, PackageError, zipfile.BadZipFile):
            package.state = PackageState.QUARANTINED
            package.updated_at = _now()
            quarantined += 1

    staged_parts = sum(1 for _ in paths.staging_root.glob("*.zip.part"))
    return ReconciliationResult(adopted, quarantined, staged_parts)


def write_manifest(
    identity: PackageIdentity,
    prepared_at: datetime,
    provenance: PackageProvenance,
    artifacts: Iterable[PackageArtifact],
) -> bytes:
    timestamp = _format_timestamp(prepared_at)
    _validate_provenance(provenance)
    ordered_artifacts = tuple(sorted(artifacts, key=lambda artifact: artifact.name))
    _validate_artifacts(ordered_artifacts)
    serialized_artifacts: list[dict[str, int | str]] = []
    for artifact in ordered_artifacts:
        item: dict[str, int | str] = {
            "name": artifact.name,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
        }
        if artifact.row_count is not None:
            item["row_count"] = artifact.row_count
        serialized_artifacts.append(item)
    payload = {
        "artifacts": serialized_artifacts,
        "package": {
            "id": str(identity.id),
            "kind": identity.kind,
            "schema_version": "v1",
            "version": identity.version,
        },
        "prepared_at": timestamp,
        "provenance": {
            "configuration_fingerprint": provenance.configuration_fingerprint,
            "raw_source_sha256": sorted(provenance.raw_source_sha256),
            "source_format_versions": sorted(provenance.source_format_versions),
        },
    }
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def write_preparation_report(findings: Iterable[PreparationFinding]) -> bytes:
    ordered = sorted(
        findings,
        key=lambda finding: (
            _severity_rank(finding.severity),
            finding.code,
            finding.subject_type,
            finding.subject_id,
            finding.message,
        ),
    )
    lines = ["severity,code,subject_type,subject_id,message"]
    for finding in ordered:
        _validate_finding(finding)
        lines.append(
            _csv_row(
                (
                    finding.severity,
                    finding.code,
                    finding.subject_type,
                    finding.subject_id,
                    finding.message,
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def inspect_archive(path: Path, identity: PackageIdentity) -> PublishedArchive:
    """Reopen and validate every ZIP member against its manifest."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            raise PackageError("archive members are not deterministic and unique")
        if "manifest.json" not in names or any(
            name.endswith(".part") for name in names
        ):
            raise PackageError("archive has an invalid member list")
        contents = {name: archive.read(name) for name in names}
        if archive.testzip() is not None:
            raise PackageError("archive member checksum failed")

    manifest = _parse_manifest(contents["manifest.json"], identity)
    artifact_items = manifest["artifacts"]
    if not isinstance(artifact_items, list):
        raise PackageError("manifest artifacts are invalid")
    artifact_names: list[str] = []
    for item in artifact_items:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise PackageError("manifest artifacts are invalid")
        artifact_names.append(item["name"])
    if set(artifact_names) | {"manifest.json"} != set(contents):
        raise PackageError("manifest filenames do not match archive members")
    artifacts = tuple(
        _artifact_from_content(name, contents[name]) for name in artifact_names
    )
    expected_artifacts = tuple(sorted(artifacts, key=lambda artifact: artifact.name))
    if artifact_names != [artifact.name for artifact in expected_artifacts]:
        raise PackageError("manifest artifacts are not sorted")
    if [_artifact_dict(artifact) for artifact in expected_artifacts] != artifact_items:
        raise PackageError("manifest checksums, sizes, or row counts do not match")
    state = _state_from_report(contents["preparation_report.csv"])
    return PublishedArchive(
        "", sha256_file(path), path.stat().st_size, expected_artifacts, state
    )


def _build_archive(
    specification: PackageSpecification,
) -> tuple[bytes, tuple[PackageArtifact, ...]]:
    _validate_specification(specification)
    report = write_preparation_report(specification.findings)
    members = {artifact.name: artifact.content for artifact in specification.artifacts}
    members["preparation_report.csv"] = report
    artifacts = tuple(
        sorted(
            (
                _artifact_from_content(name, content)
                for name, content in members.items()
            ),
            key=lambda artifact: artifact.name,
        )
    )
    manifest = write_manifest(
        specification.identity,
        specification.prepared_at,
        specification.provenance,
        artifacts,
    )
    members["manifest.json"] = manifest
    return _build_zip_archive(members), artifacts


def _build_zip_archive(members: Mapping[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                members[name],
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    return buffer.getvalue()


def _record_ready_package(
    database: Session, package: Package, published: PublishedArchive
) -> None:
    package.state = published.state
    package.relative_path = published.relative_path
    package.size_bytes = published.size_bytes
    package.sha256 = published.sha256
    package.updated_at = _now()
    database.execute(delete(PackageFile).where(PackageFile.package_id == package.id))
    for artifact in published.artifacts:
        database.add(
            PackageFile(
                package_id=package.id,
                name=artifact.name,
                sha256=artifact.sha256,
                size_bytes=artifact.size_bytes,
                row_count=artifact.row_count,
            )
        )
    database.flush()


def _validate_package_record(package: Package, identity: PackageIdentity) -> None:
    if (
        package.id != identity.id
        or package.kind != identity.kind
        or package.version != identity.version
        or package.state != PackageState.BUILDING
    ):
        raise PackageError("package record is not an eligible BUILDING package")


def _validate_specification(specification: PackageSpecification) -> None:
    if specification.identity.version < 1:
        raise PackageError("package version must be positive")
    expected = {
        PackageKind.DAILY: {"equity_market_data.csv", "index_ohlc.csv"},
        PackageKind.UNIVERSE: {"universe.csv"},
        PackageKind.BACKFILL: {"universe.csv", "index_ohlc.csv"},
    }[specification.identity.kind]
    names = [artifact.name for artifact in specification.artifacts]
    if len(names) != len(set(names)) or not expected.issubset(names):
        raise PackageError("package artifacts do not match the required package kind")
    if specification.identity.kind != PackageKind.BACKFILL and set(names) != expected:
        raise PackageError("package artifacts do not match the required package kind")
    if specification.identity.kind == PackageKind.BACKFILL and any(
        name not in expected
        and re.fullmatch(r"equity_market_data_[0-9]{4}\.csv", name) is None
        for name in names
    ):
        raise PackageError("backfill artifacts do not match the required package kind")
    if any(
        name == "preparation_report.csv" or name == "manifest.json" for name in names
    ):
        raise PackageError("generated package members cannot be supplied as artifacts")
    for artifact in specification.artifacts:
        _validate_safe_name(artifact.name)
        if not artifact.content:
            raise PackageError("package artifacts must not be empty")
        _csv_row_count(artifact.name, artifact.content)


def _validate_artifacts(artifacts: Sequence[PackageArtifact]) -> None:
    names = [artifact.name for artifact in artifacts]
    if names != sorted(names) or len(names) != len(set(names)):
        raise PackageError("artifact metadata must be uniquely sorted")
    for artifact in artifacts:
        _validate_safe_name(artifact.name)
        if artifact.size_bytes < 1 or _DIGEST.fullmatch(artifact.sha256) is None:
            raise PackageError("artifact metadata is invalid")
        if artifact.name.endswith(".csv"):
            if artifact.row_count is None or artifact.row_count < 0:
                raise PackageError("CSV artifact row count is invalid")
        elif artifact.row_count is not None:
            raise PackageError("non-CSV artifact cannot have a row count")


def _artifact_from_content(name: str, content: bytes) -> PackageArtifact:
    _validate_safe_name(name)
    if not content:
        raise PackageError("archive artifact is empty")
    row_count = _csv_row_count(name, content) if name.endswith(".csv") else None
    return PackageArtifact(name, sha256(content).hexdigest(), len(content), row_count)


def _csv_row_count(name: str, content: bytes) -> int:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackageError("canonical CSV is not UTF-8") from error
    if not text.endswith("\n") or "\r" in text:
        raise PackageError("canonical CSV must use LF and a final newline")
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows or not rows[0]:
        raise PackageError("canonical CSV must have a header")
    header = tuple(rows[0])
    expected_header, key_columns, optional_columns = _csv_contract(name)
    if header != expected_header:
        raise PackageError("canonical CSV schema is not recognised")
    keys: set[tuple[str, ...]] = set()
    for row in rows[1:]:
        if len(row) != len(header):
            raise PackageError("canonical CSV row does not match its header")
        values = dict(zip(header, row, strict=True))
        for column, value in values.items():
            if not value or (value == "NA" and column not in optional_columns):
                raise PackageError("canonical CSV has a missing required value")
        key = tuple(values[column] for column in key_columns)
        if key in keys:
            raise PackageError("canonical CSV has duplicate business keys")
        keys.add(key)
    return len(rows) - 1


def _csv_contract(name: str) -> tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]:
    if name == "equity_market_data.csv" or re.fullmatch(
        r"equity_market_data_[0-9]{4}\.csv", name
    ):
        return (
            EQUITY_SCHEMA.header,
            EQUITY_SCHEMA.sort_key,
            EQUITY_SCHEMA.optional_columns,
        )
    if name == "index_ohlc.csv":
        return (
            INDEX_SCHEMA.header,
            INDEX_SCHEMA.sort_key,
            INDEX_SCHEMA.optional_columns,
        )
    if name == "universe.csv":
        return (
            UNIVERSE_SCHEMA.header,
            UNIVERSE_SCHEMA.sort_key,
            UNIVERSE_SCHEMA.optional_columns,
        )
    if name == "preparation_report.csv":
        return _PREPARATION_HEADER, _PREPARATION_HEADER, frozenset()
    raise PackageError("canonical CSV filename is not approved")


def _parse_manifest(content: bytes, identity: PackageIdentity) -> Mapping[str, object]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackageError("manifest is not UTF-8 JSON") from error
    if not isinstance(payload, dict):
        raise PackageError("manifest root is invalid")
    package = payload.get("package")
    if not isinstance(package, dict) or package != {
        "id": str(identity.id),
        "kind": identity.kind,
        "schema_version": "v1",
        "version": identity.version,
    }:
        raise PackageError("manifest package identity is invalid")
    if content != _canonical_json(payload):
        raise PackageError("manifest representation is not deterministic")
    return payload


def _artifact_dict(artifact: PackageArtifact) -> dict[str, int | str]:
    result: dict[str, int | str] = {
        "name": artifact.name,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
    }
    if artifact.row_count is not None:
        result["row_count"] = artifact.row_count
    return result


def _state_from_report(content: bytes) -> PackageState:
    try:
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8"), newline="")))
    except UnicodeDecodeError as error:
        raise PackageError("preparation report is not UTF-8") from error
    if any(row.get("severity") == FindingSeverity.ERROR for row in rows):
        raise PackageError("archive contains a blocking preparation error")
    if any(row.get("severity") == FindingSeverity.WARNING for row in rows):
        return PackageState.READY_WITH_WARNINGS
    return PackageState.READY


def _ready_path_from_record(paths: StoragePaths, package: Package) -> Path:
    if package.relative_path is None:
        raise PackageError("ready package path is missing")
    expected = paths.ready_package(package.kind, str(package.id))
    relative = PurePosixPath(package.relative_path)
    if relative.is_absolute() or expected != paths.resolve_under(
        paths.root, package.relative_path
    ):
        raise PackageError("ready package path is unsafe")
    return expected


def _validate_provenance(provenance: PackageProvenance) -> None:
    if _DIGEST.fullmatch(provenance.configuration_fingerprint) is None:
        raise PackageError("configuration fingerprint is not SHA-256")
    if not provenance.raw_source_sha256 or not provenance.source_format_versions:
        raise PackageError("package provenance is incomplete")
    if any(_DIGEST.fullmatch(value) is None for value in provenance.raw_source_sha256):
        raise PackageError("raw source digest is invalid")
    if any(not value.strip() for value in provenance.source_format_versions):
        raise PackageError("source format version is invalid")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.microsecond != 0:
        raise PackageError("prepared_at must be timezone-aware whole seconds")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_finding(finding: PreparationFinding) -> None:
    if _FINDING_CODE.fullmatch(finding.code) is None:
        raise PackageError("preparation finding code is invalid")
    if finding.subject_type not in _FINDING_SUBJECTS:
        raise PackageError("preparation finding subject type is invalid")
    if not finding.subject_id.strip() or not finding.message.strip():
        raise PackageError("preparation finding fields are required")


def _severity_rank(severity: FindingSeverity) -> int:
    return {
        FindingSeverity.ERROR: 0,
        FindingSeverity.WARNING: 1,
        FindingSeverity.INFO: 2,
    }[severity]


def _validate_safe_name(name: str) -> None:
    path = PurePosixPath(name)
    if (
        path.name != name
        or path.suffix == ".part"
        or name in {"", "manifest.json"}
        or "\\" in name
    ):
        raise PackageError("package member name is unsafe")


def _csv_row(values: Sequence[str]) -> str:
    return ",".join(_csv_cell(value) for value in values)


def _csv_cell(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise PackageError("preparation report fields are required")
    if normalized == "NA" or any(character in normalized for character in ',"\r\n'):
        return '"' + normalized.replace('"', '""') + '"'
    return normalized


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _now() -> datetime:
    return datetime.now(UTC)
