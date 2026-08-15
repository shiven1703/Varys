import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("module", ["varys.api", "varys.worker"])
def test_bootstrap_processes_start_independently(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module, "--check"],
        check=False,
        capture_output=True,
        env=os.environ.copy(),
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "bootstrap complete" in result.stdout
