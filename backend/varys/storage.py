"""Safe, durable filesystem primitives for Varys-managed data."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_SHA256 = re.compile(r"[0-9a-f]{64}")
_PACKAGE_KINDS = frozenset({"daily", "universe", "backfill"})


@dataclass(frozen=True, slots=True)
class StorageReadiness:
    ready: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StoragePaths:
    root: Path

    @classmethod
    def from_root(cls, root: Path) -> StoragePaths:
        if not root.is_absolute():
            raise ValueError("VARYS_DATA_ROOT must be an absolute path")
        return cls(root.resolve())

    @property
    def raw_root(self) -> Path:
        return self.root / "raw" / "sha256"

    @property
    def work_root(self) -> Path:
        return self.root / "work"

    @property
    def staging_root(self) -> Path:
        return self.root / "packages" / "staging"

    @property
    def ready_root(self) -> Path:
        return self.root / "packages" / "ready"

    def raw_artifact(self, digest: str) -> Path:
        _validate_sha256(digest)
        return self.resolve_under(self.raw_root, f"{digest[:2]}/{digest}")

    def run_workspace(self, run_id: str) -> Path:
        return self.resolve_under(self.work_root, _validate_uuid(run_id))

    def create_run_workspace(self, run_id: str) -> Path:
        workspace = self.run_workspace(run_id)
        workspace.mkdir(parents=True, exist_ok=False)
        return workspace

    def staging_package(self, package_id: str) -> Path:
        return self.resolve_under(
            self.staging_root, f"{_validate_uuid(package_id)}.zip.part"
        )

    def ready_package(self, package_kind: str, package_id: str) -> Path:
        if package_kind not in _PACKAGE_KINDS:
            raise ValueError("package kind is not approved")
        return self.resolve_under(
            self.ready_root / package_kind, f"{_validate_uuid(package_id)}.zip"
        )

    def resolve_under(self, approved_root: Path, relative_path: str) -> Path:
        relative = PurePosixPath(relative_path)
        if (
            relative.is_absolute()
            or "\\" in relative_path
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ValueError("path must be a safe relative path")

        resolved_root = approved_root.resolve()
        if not resolved_root.is_relative_to(self.root):
            raise ValueError("approved root escapes storage root")
        candidate = (resolved_root / Path(*relative.parts)).resolve()
        if not candidate.is_relative_to(resolved_root):
            raise ValueError("path escapes approved root")
        return candidate


def initialize_storage(paths: StoragePaths) -> None:
    for directory in (
        paths.raw_root,
        paths.work_root,
        paths.staging_root,
        paths.ready_root / "daily",
        paths.ready_root / "universe",
        paths.ready_root / "backfill",
        paths.root / "quarantine",
        paths.root / "diagnostics",
    ):
        directory.mkdir(parents=True, exist_ok=True)


def check_storage_readiness(data_root: Path | None) -> StorageReadiness:
    if data_root is None:
        return StorageReadiness(False, "data root is not configured")
    if not data_root.is_absolute() or not data_root.is_dir():
        return StorageReadiness(False, "data root is missing")

    paths = StoragePaths.from_root(data_root)
    required_directories = (
        paths.raw_root,
        paths.work_root,
        paths.staging_root,
        paths.ready_root,
    )
    if any(not directory.is_dir() for directory in required_directories):
        return StorageReadiness(False, "required storage paths are missing")

    probe = paths.root / ".readiness.part"
    try:
        descriptor = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(descriptor, b"ok")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        probe.unlink()
        _fsync_directory(paths.root)
    except OSError as error:
        return StorageReadiness(
            False, f"data root is not writable: {error.__class__.__name__}"
        )
    return StorageReadiness(True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_durable_bytes(destination: Path, content: bytes) -> Path:
    part_path = destination.with_name(f"{destination.name}.part")
    if part_path.exists() or destination.exists():
        raise FileExistsError("destination or durable part file already exists")

    with part_path.open("xb") as file_handle:
        file_handle.write(content)
        file_handle.flush()
        os.fsync(file_handle.fileno())
    return part_path


def atomic_publish(part_path: Path, destination: Path) -> None:
    if part_path.suffix != ".part":
        raise ValueError("publication source must be a .part file")
    if destination.exists():
        raise FileExistsError("ready destination already exists")
    if part_path.parent.stat().st_dev != destination.parent.stat().st_dev:
        raise ValueError("atomic publication requires the same filesystem")

    os.replace(part_path, destination)
    _fsync_directory(destination.parent)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validate_uuid(value: str) -> str:
    parsed = uuid.UUID(value)
    if str(parsed) != value:
        raise ValueError("identifier must be a canonical UUID")
    return value


def _validate_sha256(value: str) -> None:
    if _SHA256.fullmatch(value) is None:
        raise ValueError("digest must be lowercase SHA-256")
