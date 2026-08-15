import sys


def test_supported_python_version() -> None:
    assert sys.version_info[:2] == (3, 12)
