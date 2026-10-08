"""Single redaction function for all docsync output (FR-6, NFR-10).

``cli.py`` is the only caller (the single choke point). Every regex quantifier is
explicitly bounded and there are no nested or overlapping unbounded repeats, so the work
done is linear in the input size (T20, CR-1). All patterns are compiled once, at import.
"""

import re
from collections.abc import Callable, Iterable

PLACEHOLDER = "[REDACTED]"

_Replacement = str | Callable[["re.Match[str]"], str]


def _redact_sk_key(match: "re.Match[str]") -> str:
    """Redact an ``sk-`` key only if it contains a digit (spares names such as ``sk-learn-x``)."""
    text = match.group(0)
    return PLACEHOLDER if any(c.isdigit() for c in text) else text


def _is_word_like(segment: str) -> bool:
    """A long segment of letters (optional digit suffix) that is mostly lower case, like words."""
    letters = segment.rstrip("0123456789")
    upper = sum(1 for c in letters if c.isupper())
    return len(segment) >= 8 and letters.isalpha() and upper <= 0.3 * len(letters)


def _is_path_like(run: str) -> bool:
    """True if ``run`` looks like a URL tail or file path: 2+ word-like ``/`` segments.

    Random base64 is about half upper case, so its fragments are rarely word-like.
    """
    return sum(1 for segment in run.split("/") if _is_word_like(segment)) >= 2


def _redact_mixed_case_blob(match: "re.Match[str]") -> str:
    """Redact a long base64 run only if it has an uppercase, a lowercase and a digit character.

    A heuristic: it leaves plain hex (for example a SHA-256) and URL or path tails alone,
    because a missed secret in a committed document is permanent while a false positive
    is cosmetic and reversible.
    """
    run = match.group(0)
    mixed = any(c.isupper() for c in run) and any(c.islower() for c in run)
    if mixed and any(c.isdigit() for c in run) and not _is_path_like(run):
        return PLACEHOLDER
    return run


def _rule(
    pattern: str, replacement: _Replacement, flags: int = 0
) -> tuple[re.Pattern[str], _Replacement]:
    return re.compile(pattern, flags), replacement


_KEEP_PREFIX = rf"\1{PLACEHOLDER}"
_SCHEME = r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]{0,31}://)"
_STRONG = r"(?:token|secret|password|passwd|credential)"
# A strong key name may be plural or carry a separated suffix (SECRET_KEY, passwords), may be
# quoted (JSON/YAML), and is followed by ':' or '='. "tokenizer" and "secretary" do not match.
_STRONG_KEY = rf"{_STRONG}s?(?:[_.-][A-Za-z0-9_.-]{{0,32}})?[\"']?[ \t]{{0,8}}[:=][ \t]{{0,8}}"
_VALUE = (
    r"(?:\"[^\"\n]{0,256}\"?[^\s,;|}]{0,256}"
    r"|'[^'\n]{0,256}'?[^\s,;|}]{0,256}"
    r"|[^\s,;|}\"']{1,256})"
)

# Order matters (docs/02-architecture.md section 7): provider tokens, then header and URL
# credentials, then key=value pairs, then the generic blob heuristic last.
_RULES: tuple[tuple[re.Pattern[str], _Replacement], ...] = (
    _rule(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,255}", PLACEHOLDER),
    _rule(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,255}", _redact_sk_key),
    _rule(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])", PLACEHOLDER),
    _rule(r"xox[baprs]-[A-Za-z0-9-]{10,200}", PLACEHOLDER),
    _rule(
        r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,2048}\.[A-Za-z0-9_-]{8,2048}"
        r"(?:\.[A-Za-z0-9_-]{0,2048})?",
        PLACEHOLDER,
    ),
    _rule(r"-----BEGIN [A-Z ]{0,40}PRIVATE KEY-----[A-Za-z0-9+/=\r\n]{0,8192}", PLACEHOLDER),
    _rule(
        r"(authorization[ \t]{0,8}:[ \t]{0,8})(?:(?:bearer|basic|token|digest)[ \t]{1,8})?"
        r"[^\s|]{1,2048}",
        _KEEP_PREFIX,
        re.IGNORECASE,
    ),
    _rule(r"\b(bearer[ \t]{1,8})[A-Za-z0-9._~+/=-]{8,2048}", _KEEP_PREFIX, re.IGNORECASE),
    _rule(_SCHEME + r"[^\s/@:]{1,256}:[^\s/@]{1,256}@", rf"\1{PLACEHOLDER}@"),
    _rule(_SCHEME + r"[A-Za-z0-9_.~%+-]{20,256}@", rf"\1{PLACEHOLDER}@"),
    _rule(rf"({_STRONG_KEY}){_VALUE}", _KEEP_PREFIX, re.IGNORECASE),
    _rule(
        r"(key[\"']?[ \t]{0,8}[:=][ \t]{0,8})[\"']?[A-Za-z0-9_+/=.-]{20,256}[\"']?",
        _KEEP_PREFIX,
        re.IGNORECASE,
    ),
    # Markdown table: a cell that is exactly a strong key name, then the value in the next cell.
    _rule(
        rf"(\|[ \t]{{0,8}}{_STRONG}s?[ \t]{{0,8}}\|[ \t]{{0,8}})[^|\n]{{1,256}}?(?=[ \t]{{0,8}}\|)",
        _KEEP_PREFIX,
        re.IGNORECASE,
    ),
    _rule(r"[A-Za-z0-9+/]{40,4096}={0,2}", _redact_mixed_case_blob),
)


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Return ``text`` with secret-looking values replaced by ``PLACEHOLDER``.

    Pure: reads no environment. Literal ``secrets`` go first (longest first; empty or
    whitespace-only entries ignored), then every rule in ``_RULES`` in order. Redacting
    already-redacted text changes nothing for ordinary input; this is checked by tests and
    a property fuzz but is not proven for arbitrary adversarial strings.
    """
    literals = sorted({s.strip() for s in secrets if s.strip()}, key=len, reverse=True)
    for literal in literals:
        text = text.replace(literal, PLACEHOLDER)
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    return text
