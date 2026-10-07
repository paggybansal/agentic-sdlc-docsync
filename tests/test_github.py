"""Tests for docsync.github (T8: offline decision logic)."""

from typing import Any

import pytest
import requests

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


_TOKEN = "tok-SECRET-value-123"


class FakeResponse:
    """Minimal stand-in for ``requests.Response`` (``status_code`` and ``json()``)."""

    def __init__(self, status_code: int = 200, payload: Any = None, bad_json: bool = False) -> None:
        self.status_code = status_code
        self._payload = payload
        self._bad_json = bad_json

    def json(self) -> Any:
        if self._bad_json:
            raise requests.JSONDecodeError("Expecting value", "doc", 0)
        return self._payload


def _online(response: Any = None, error: Exception | None = None) -> tuple[Any, FakeSession]:
    session = FakeSession(response=response, error=error)
    return fetch("octo/demo", False, _TOKEN, session), session


def _assert_degraded(result: Any, session: FakeSession) -> None:
    hosted, warnings = result
    assert set(hosted.values()) == {NOT_FOUND}
    assert list(hosted) == list(HOSTED_KEYS)
    assert len(warnings) == 1
    assert len(session.calls) == 1
    assert _TOKEN not in warnings[0]


def test_online_request_makes_exactly_one_get_with_fixed_url() -> None:
    # Arrange / Act
    _, session = _online(FakeResponse(404))

    # Assert
    assert [c[0] for c in session.calls] == ["https://api.github.com/repos/octo/demo"]


def test_online_request_uses_timeout_of_5_seconds() -> None:
    # Arrange / Act
    _, session = _online(FakeResponse(404))

    # Assert
    assert session.calls[0][2] == 5


def test_online_request_sends_bearer_authorization_header() -> None:
    # Arrange / Act
    _, session = _online(FakeResponse(404))

    # Assert
    assert session.calls[0][1] == {"Authorization": f"Bearer {_TOKEN}"}


def test_online_request_strips_whitespace_around_token_and_repo() -> None:
    # Arrange
    session = FakeSession(response=FakeResponse(404))

    # Act
    fetch(" octo/demo ", False, f" {_TOKEN}\n", session)

    # Assert
    assert session.calls[0][0].endswith("/repos/octo/demo")
    assert session.calls[0][1]["Authorization"] == f"Bearer {_TOKEN}"


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout("t"),
        requests.ConnectTimeout("t"),
        requests.ReadTimeout("t"),
        requests.ConnectionError("c"),
        requests.exceptions.SSLError("s"),
        requests.TooManyRedirects("r"),
        requests.RequestException("x"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_ec_1_request_exception_degrades_with_one_warning(error: Exception) -> None:
    # Arrange / Act
    result, session = _online(error=error)

    # Assert
    _assert_degraded(result, session)


def test_ec_1_timeout_warning_says_timed_out() -> None:
    # Arrange / Act
    (_, warnings), _ = _online(error=requests.Timeout("t"))

    # Assert
    assert "timed out" in warnings[0]


def test_ec_1_mocked_timeout_returns_without_waiting() -> None:
    # Arrange: FakeSession raises immediately, so no real 5 s wait (supports NFR-2)
    # Act
    result, session = _online(error=requests.Timeout("t"))

    # Assert
    assert len(session.calls) == 1
    assert session.calls[0][2] == 5
    assert set(result[0].values()) == {NOT_FOUND}


def test_ec_1_exception_text_and_token_are_never_echoed() -> None:
    # Arrange
    error = requests.ConnectionError(f"https://api.github.com failed Bearer {_TOKEN}")

    # Act
    (_, warnings), _ = _online(error=error)

    # Assert
    assert _TOKEN not in warnings[0]
    assert "api.github.com" not in warnings[0]


def test_ec_2_api_404_degrades() -> None:
    # Arrange / Act
    result, session = _online(FakeResponse(404))

    # Assert
    _assert_degraded(result, session)
    assert "404" in result[1][0]


def test_ec_3_api_403_rate_limit_degrades() -> None:
    # Arrange / Act
    result, session = _online(FakeResponse(403))

    # Assert
    _assert_degraded(result, session)
    assert "403" in result[1][0]


def test_non_2xx_status_other_than_404_403_degrades() -> None:
    # Arrange / Act
    result, session = _online(FakeResponse(500))

    # Assert
    _assert_degraded(result, session)
    assert "500" in result[1][0]


def test_ec_4_invalid_json_degrades() -> None:
    # Arrange / Act
    result, session = _online(FakeResponse(200, bad_json=True))

    # Assert
    _assert_degraded(result, session)


@pytest.mark.parametrize("payload", [[], ["a"], "text", 5, None], ids=repr)
def test_ec_4_non_object_json_payload_degrades(payload: Any) -> None:
    # Arrange / Act
    result, session = _online(FakeResponse(200, payload))

    # Assert
    _assert_degraded(result, session)


def test_online_failure_makes_no_retry() -> None:
    # Arrange / Act
    _, session = _online(error=requests.ConnectionError("c"))

    # Assert
    assert len(session.calls) == 1
