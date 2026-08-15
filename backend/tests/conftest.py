"""Deterministic test defaults."""

from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def prohibit_network(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    if request.node.get_closest_marker("integration") is not None:
        return

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("network access is prohibited in tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
