"""Command-line interface: argument parsing and validation (FR-18, FR-19)."""

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from docsync.errors import UsageError
from docsync.redact import redact

_GITHUB_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class CliArgs:
    """Validated command-line arguments."""

    command: str
    repo: Path
    out: Path
    github_repo: str | None
    offline: bool
    verbose: bool


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    """Build the ``docsync generate|check`` parser; usage errors raise ``UsageError``."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".", help="repository root to document")
    common.add_argument("--out", default="docs/PROJECT_DOCS.md", help="output file")
    common.add_argument("--github-repo", default=None, help="OWNER/NAME for hosted metadata")
    common.add_argument("--offline", action="store_true", help="make no network calls")
    common.add_argument("--verbose", action="store_true", help="extra diagnostics on stderr")
    parser = _Parser(prog="docsync", description="Keep project docs in sync with the repo.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate", parents=[common], help="write the document")
    commands.add_parser("check", parents=[common], help="exit 1 if the document is stale")
    return parser


def _valid_github_repo(value: str) -> bool:
    owner, _, name = value.partition("/")
    dots = {".", ".."}
    return bool(_GITHUB_REPO.fullmatch(value)) and owner not in dots and name not in dots


def parse_args(argv: Sequence[str] | None = None) -> CliArgs:
    """Parse and validate ``argv``; raise ``UsageError`` on any invalid input."""
    ns = build_parser().parse_args(argv)
    if not Path(ns.repo).is_dir():
        raise UsageError(f"--repo is not an existing directory: {ns.repo!r}")
    if ns.github_repo is not None and not _valid_github_repo(ns.github_repo):
        raise UsageError(f"--github-repo must look like OWNER/NAME, got {ns.github_repo!r}")
    return CliArgs(ns.command, Path(ns.repo), Path(ns.out), ns.github_repo, ns.offline, ns.verbose)


def main(argv: Sequence[str] | None = None) -> int:
    """Console entry point; returns the process exit code."""
    try:
        parse_args(argv)
    except UsageError as exc:
        print(redact(f"docsync: error: {exc}"), file=sys.stderr)
        return 2
    # TEMPORARY loud guard: removed by T14 (generate) and T16 (check); must not survive step 5.
    raise NotImplementedError("generate is implemented in task T14, check in task T16")
