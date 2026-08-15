from pathlib import Path
from unittest.mock import patch

import pytest

from varys.storage import (
    StoragePaths,
    StorageReadiness,
    atomic_publish,
    check_storage_readiness,
    initialize_storage,
    sha256_file,
    write_durable_bytes,
)


def test_safe_paths_reject_traversal_and_symlink_escape(tmp_path: Path) -> None:
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)
    outside = tmp_path / "outside"
    outside.mkdir()
    (paths.work_root / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError):
        paths.resolve_under(paths.work_root, "../outside")
    with pytest.raises(ValueError):
        paths.resolve_under(paths.work_root, "escape/file.txt")
    with pytest.raises(ValueError):
        paths.run_workspace("not-a-uuid")


def test_durable_write_remains_part_until_atomic_publish(tmp_path: Path) -> None:
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)
    destination = paths.staging_root / "artifact.zip"

    part_path = write_durable_bytes(destination, b"verified bytes")

    assert part_path.exists()
    assert not destination.exists()
    assert sha256_file(part_path) == (
        "186287b2d987891f027b4bc8baaf621a3e5a4a73ec78e04b0f65dc309b1ccc03"
    )

    atomic_publish(part_path, destination)

    assert destination.read_bytes() == b"verified bytes"
    assert not part_path.exists()


def test_failed_durable_write_never_creates_destination(tmp_path: Path) -> None:
    destination = tmp_path / "artifact.csv"

    with patch("varys.storage.os.fsync", side_effect=OSError("disk failure")):
        with pytest.raises(OSError, match="disk failure"):
            write_durable_bytes(destination, b"partial")

    assert not destination.exists()
    assert destination.with_name("artifact.csv.part").exists()


def test_storage_readiness_detects_missing_and_unwritable_roots(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"
    assert check_storage_readiness(missing_root) == StorageReadiness(
        False, "data root is missing"
    )

    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)
    with patch("varys.storage.os.open", side_effect=PermissionError("denied")):
        readiness = check_storage_readiness(paths.root)

    assert readiness.ready is False
    assert readiness.reason == "data root is not writable: PermissionError"
