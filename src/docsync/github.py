"""GitHub client: decides offline vs online and returns the six hosted fields."""

from typing import Any, Protocol

import requests

from docsync.model import NOT_FOUND, FieldValue

HOSTED_KEYS = ("full_name", "description", "default_branch", "visibility", "license", "topics")

_API_BASE = "https://api.github.com/repos/"
_TIMEOUT = 5
_STATUS_TEXT = {
    404: "repository not found (HTTP 404)",
    403: "access denied or rate limited (HTTP 403)",
}


class HttpSession(Protocol):
    """The one method of ``requests.Session`` that this module uses."""

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> Any:
        """Perform a GET request."""


def _unresolved() -> dict[str, FieldValue]:
    return dict.fromkeys(HOSTED_KEYS, NOT_FOUND)


def _get_payload(http: HttpSession, url: str, token: str) -> tuple[dict[str, Any] | None, str]:
    """One GET; returns ``(payload, "")`` or ``(None, fixed failure text)``."""
    try:
        response = http.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=_TIMEOUT)
    except requests.Timeout:
        return None, "request timed out"
    except requests.RequestException:
        return None, "request failed"
    status = response.status_code
    if not 200 <= status < 300:
        return None, _STATUS_TEXT.get(status, f"unexpected HTTP status {status}")
    try:
        payload = response.json()
    except ValueError:
        return None, "response was not valid JSON"
    if not isinstance(payload, dict):
        return None, "response was not a JSON object"
    return payload, ""


def _extract(payload: dict[str, Any]) -> dict[str, FieldValue]:
    raise NotImplementedError("field extraction is implemented in task T10")


def fetch(
    github_repo: str | None,
    offline: bool,
    token: str | None,
    session: HttpSession | None = None,
) -> tuple[dict[str, FieldValue], tuple[str, ...]]:
    """Return ``(hosted, warnings)`` for ``github_repo``.

    No request is made when ``offline`` is set (it wins over a set token), the token is
    unset or blank, or ``github_repo`` is omitted; every hosted field is then ``Not Found``.
    Otherwise one GET (5 s timeout, no retry) is made; any failure gives one fixed-text
    warning and all fields ``Not Found``. Exception text is never echoed.
    """
    if offline or not (token and token.strip()) or not (github_repo and github_repo.strip()):
        return _unresolved(), ()
    http = session if session is not None else requests.Session()
    payload, failure = _get_payload(http, _API_BASE + github_repo.strip(), token.strip())
    if payload is None:
        return _unresolved(), (f"GitHub lookup failed: {failure}; hosted fields are Not Found",)
    return _extract(payload), ()
