import socket

import pytest


def test_uncontrolled_network_access_is_prohibited() -> None:
    with pytest.raises(RuntimeError, match="network access is prohibited"):
        socket.create_connection(("example.com", 443))
