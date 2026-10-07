"""Single redaction function for all docsync output (FR-6, NFR-10)."""

import re
from collections.abc import Iterable

PLACEHOLDER = "[REDACTED]"

_TOKEN_PREFIXES = re.compile(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+")
_AUTH_HEADER = re.compile(
    r"(authorization[ \t]*:[ \t]*)(?:(?:bearer|basic|token|digest)[ \t]+)?[^\s|]+", re.IGNORECASE
)
_BEARER = re.compile(r"\b(bearer[ \t]+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_URL_USERINFO = re.compile(r"([a-z][a-z0-9+.-]*://)[^\s/@:]+:[^\s/@]+@", re.IGNORECASE)
_KEY_VALUE = re.compile(
    r"\b([\w.-]*(?:token|secret|password|passwd|key|credential)[\w.-]*)([ \t]*[:=][ \t]*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;|\"']+)",
    re.IGNORECASE,
)


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Return ``text`` with secret-looking values replaced by ``PLACEHOLDER``.

    Pure: reads no environment. Order: literal ``secrets`` (longest first; empty or
    whitespace-only entries ignored), token prefixes, ``Authorization`` header values,
    ``Bearer`` values, URL userinfo, then ``key=value`` / ``key: value`` pairs.
    """
    literals = sorted({s.strip() for s in secrets if s.strip()}, key=len, reverse=True)
    for literal in literals:
        text = text.replace(literal, PLACEHOLDER)
    text = _TOKEN_PREFIXES.sub(PLACEHOLDER, text)
    text = _AUTH_HEADER.sub(rf"\1{PLACEHOLDER}", text)
    text = _BEARER.sub(rf"\1{PLACEHOLDER}", text)
    text = _URL_USERINFO.sub(rf"\1{PLACEHOLDER}@", text)
    return _KEY_VALUE.sub(rf"\1\2{PLACEHOLDER}", text)
