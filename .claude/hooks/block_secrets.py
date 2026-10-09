"""PreToolUse hook: deny any agent write/edit targeting a secret-bearing file.

Reads the tool-call payload from stdin. Exit code 2 blocks the tool call and sends
stderr back to the agent as feedback.
"""
from __future__ import annotations

import json
import re
import sys

BLOCKED_PATTERNS = [
    r"(^|/)\.env($|\.local$|\.production$)",
    r"\.pem$",
    r"\.key$",
    r"\.p12$",
    r"\.pfx$",
    r"(^|/)secrets?\.",
    r"(^|/)credentials?\.",
    r"(^|/)id_rsa",
]

ALLOWED_EXACT = {".env.example", ".env.sample", ".env.template"}


def target_path(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if value:
            return str(value)
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    raw_path = target_path(payload)
    if not raw_path:
        return 0

    normalised = raw_path.replace("\\", "/")
    basename = normalised.rsplit("/", 1)[-1].lower()
    if basename in ALLOWED_EXACT:
        return 0

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalised, flags=re.IGNORECASE):
            sys.stderr.write(
                "BLOCKED by hook .claude/hooks/block_secrets.py\n"
                f"Refused to write '{raw_path}': this path can hold credentials.\n"
                "Agents must never create or modify secret-bearing files.\n"
                "Use '.env.example' with empty placeholder values and read real values "
                "from environment variables at runtime.\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())