"""GitHub client: decides offline vs online and returns the six hosted fields."""

from typing import Any, Protocol

from docsync.model import NOT_FOUND, FieldValue

HOSTED_KEYS = ("full_name", "description", "default_branch", "visibility", "license", "topics")


class HttpSession(Protocol):
    """The one method of ``requests.Session`` that this module uses."""

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> Any:
        """Perform a GET request."""


def _unresolved() -> dict[str, FieldValue]:
    return dict.fromkeys(HOSTED_KEYS, NOT_FOUND)


def fetch(
    github_repo: str | None,
    offline: bool,
    token: str | None,
    session: HttpSession | None = None,
) -> tuple[dict[str, FieldValue], tuple[str, ...]]:
    """Return ``(hosted, warnings)`` for ``github_repo``.

    No request is made when ``offline`` is set (it wins over a set token), the token is
    unset or blank, or ``github_repo`` is omitted; every hosted field is then ``Not Found``.
    """
    if offline or not (token and token.strip()) or not (github_repo and github_repo.strip()):
        return _unresolved(), ()
    raise NotImplementedError("online lookup is implemented in task T9")
