from pathlib import Path
from unittest.mock import patch

import pytest

from varys.storage import atomic_publish, write_durable_bytes


def test_publish_failure_leaves_verified_part_for_recovery(tmp_path: Path) -> None:
    destination = tmp_path / "package.zip"
    part_path = write_durable_bytes(destination, b"verified bytes")

    with patch("varys.storage.os.replace", side_effect=OSError("device failure")):
        with pytest.raises(OSError, match="device failure"):
            atomic_publish(part_path, destination)

    assert part_path.read_bytes() == b"verified bytes"
    assert not destination.exists()
