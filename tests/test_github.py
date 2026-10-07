"""Tests for docsync.github (T8: offline decision logic)."""

from typing import Any

import pytest

from docsync.github import HOSTED_KEYS, fetch
from docsync.model import NOT_FOUND


class FakeSession:
    """Records ``get`` calls and returns a canned response or raises a canned error."""

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, dict[str, str], float]] = []
        self._response = response
        self._error = error

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> Any:
        self.calls.append((url, headers, timeout))
        if self._error is not None:
            raise self._error
        return self._response


def test_offline_flag_makes_no_session_calls() -> None:
    # Arrange
    session = FakeSession()

    # Act
    fetch("octo/demo", True, "tok", session)

    # Assert
    assert session.calls == []


def test_offline_flag_wins_even_if_token_is_set() -> None:
    # Arrange
    session = FakeSession()

    # Act
    hosted, warnings = fetch("octo/demo", True, "a-real-looking-token", session)

    # Assert
    assert session.calls == []
    assert set(hosted.values()) == {NOT_FOUND}
    assert warnings == ()


def test_ec_5_token_unset_makes_no_session_calls() -> None:
    # Arrange
    session = FakeSession()

    # Act
    hosted, warnings = fetch("octo/demo", False, None, session)

    # Assert
    assert session.calls == []
    assert set(hosted.values()) == {NOT_FOUND}
    assert warnings == ()


@pytest.mark.parametrize("token", ["", "   ", "\t\n"])
def test_ec_5_blank_token_is_treated_as_unset(token: str) -> None:
    # Arrange
    session = FakeSession()

    # Act
    hosted, _ = fetch("octo/demo", False, token, session)

    # Assert
    assert session.calls == []
    assert set(hosted.values()) == {NOT_FOUND}


def test_ec_14_github_repo_omitted_makes_no_session_calls() -> None:
    # Arrange
    session = FakeSession()

    # Act
    hosted, warnings = fetch(None, False, "tok", session)

    # Assert
    assert session.calls == []
    assert set(hosted.values()) == {NOT_FOUND}
    assert warnings == ()


def test_ec_14_blank_github_repo_is_treated_as_omitted() -> None:
    # Arrange
    session = FakeSession()

    # Act
    fetch("  ", False, "tok", session)

    # Assert
    assert session.calls == []


def test_offline_hosted_dict_has_exactly_the_six_keys() -> None:
    # Arrange / Act
    hosted, _ = fetch(None, True, None)

    # Assert
    assert list(hosted) == [
        "full_name", "description", "default_branch", "visibility", "license", "topics",
    ]
    assert tuple(hosted) == HOSTED_KEYS


def test_offline_without_session_argument_needs_no_network() -> None:
    # Arrange / Act
    hosted, _ = fetch("octo/demo", True, "tok")

    # Assert
    assert hosted["full_name"] == NOT_FOUND


def test_fake_session_records_call_and_returns_response() -> None:
    # Arrange
    session = FakeSession(response="resp")

    # Act
    result = session.get("https://example.test", headers={"a": "b"}, timeout=5)

    # Assert
    assert result == "resp"
    assert session.calls == [("https://example.test", {"a": "b"}, 5)]


def test_fake_session_raises_configured_error() -> None:
    # Arrange
    session = FakeSession(error=ConnectionError("boom"))

    # Act / Assert
    with pytest.raises(ConnectionError):
        session.get("https://example.test", headers={}, timeout=5)
