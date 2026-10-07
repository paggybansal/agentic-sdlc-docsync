"""Shared fixtures; the autouse fixture blocks all real network access (NFR-7)."""

import pytest
import requests


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any accidental real HTTP request fail the test."""

    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("real network access attempted in a test")

    monkeypatch.setattr(requests.Session, "request", _blocked)
