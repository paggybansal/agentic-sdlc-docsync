"""Single redaction function for all docsync output (FR-6, NFR-10)."""

import re
from collections.abc import Iterable

PLACEHOLDER = "[REDACTED]"

_TOKEN_PREFIXES = re.compile(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+")


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Return ``text`` with secret-looking values replaced by ``PLACEHOLDER``.

    Pure: reads no environment. Literal ``secrets`` are replaced longest first;
    empty or whitespace-only entries are ignored.
    """
    literals = sorted({s.strip() for s in secrets if s.strip()}, key=len, reverse=True)
    for literal in literals:
        text = text.replace(literal, PLACEHOLDER)
    return _TOKEN_PREFIXES.sub(PLACEHOLDER, text)
