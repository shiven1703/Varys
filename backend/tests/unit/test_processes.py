import os
import subprocess
import sys
from pathlib import Path

import pytest

from varys.storage import StoragePaths, check_storage_readiness


@pytest.mark.parametrize("module", ["varys.api", "varys.worker"])
def test_bootstrap_processes_start_independently(module: str, tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    environment = os.environ.copy()
    environment["VARYS_DATA_ROOT"] = str(data_root)
    result = subprocess.run(
        [sys.executable, "-m", module, "--check"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "bootstrap complete" in result.stdout
    assert check_storage_readiness(StoragePaths.from_root(data_root).root).ready is True
