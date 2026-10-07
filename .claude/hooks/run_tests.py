"""PostToolUse hook: run the test suite after any change to src/ or tests/.

Exit code 2 returns the failure output to the agent so it can self-correct without the
human having to notice and intervene.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WATCHED_PREFIXES = ("src/docsync", "tests")
MAX_OUTPUT_CHARS = 4000


def changed_path(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    return str(tool_input.get("file_path") or tool_input.get("path") or "")


def is_watched(path: str) -> bool:
    normalised = path.replace("\\", "/")
    if not normalised.endswith(".py"):
        return False
    return any(prefix in normalised for prefix in WATCHED_PREFIXES)


def has_tests() -> bool:
    tests_dir = Path("tests")
    return tests_dir.is_dir() and any(tests_dir.rglob("test_*.py"))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    path = changed_path(payload)
    if not path or not is_watched(path):
        return 0
    if not has_tests():
        print("quality gate skipped: no test files yet")
        return 0

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-x"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        sys.stderr.write(
            "POST-EDIT QUALITY GATE FAILED (.claude/hooks/run_tests.py)\n"
            f"Trigger: {path}\n\n"
            f"{result.stdout[-MAX_OUTPUT_CHARS:]}\n{result.stderr[-1000:]}\n"
            "Fix the failing test(s) before continuing to the next task.\n"
        )
        return 2

    summary = (result.stdout.strip().splitlines() or ["no output"])[-1]
    print(f"post-edit quality gate passed: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())