"""Command-line interface: parsing, validation and the generate command (FR-1, FR-18)."""

import argparse
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from docsync.collect import collect
from docsync.errors import DocsyncError, UsageError
from docsync.github import HttpSession, fetch
from docsync.model import ProjectFacts
from docsync.redact import redact
from docsync.render import render

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


def _check_out(repo: Path, out: Path) -> None:
    """``--out`` must be a ``.md`` file inside ``--repo`` (a relative path is cwd-based)."""
    if out.suffix.lower() != ".md":
        raise UsageError(f"--out must end in .md, got {str(out)!r}")
    if not out.resolve().is_relative_to(repo.resolve()):
        raise UsageError(f"--out must be inside --repo, got {str(out)!r}")


def parse_args(argv: Sequence[str] | None = None) -> CliArgs:
    """Parse and validate ``argv``; raise ``UsageError`` on any invalid input."""
    ns = build_parser().parse_args(argv)
    if not Path(ns.repo).is_dir():
        raise UsageError(f"--repo is not an existing directory: {ns.repo!r}")
    _check_out(Path(ns.repo), Path(ns.out))
    if ns.github_repo is not None and not _valid_github_repo(ns.github_repo):
        raise UsageError(f"--github-repo must look like OWNER/NAME, got {ns.github_repo!r}")
    return CliArgs(ns.command, Path(ns.repo), Path(ns.out), ns.github_repo, ns.offline, ns.verbose)


def _emit(message: str, token: str | None, *, err: bool = False) -> None:
    """Print ``message`` through the single redaction function (FR-6, FR-20)."""
    print(redact(message, secrets=(token or "",)), file=sys.stderr if err else sys.stdout)


def _generate(args: CliArgs, session: HttpSession | None) -> int:
    token = os.environ.get("DOCSYNC_GITHUB_TOKEN")
    if args.verbose:
        state = "set" if token and token.strip() else "not set"
        for line in (f"repo: {args.repo}", f"out: {args.out}", f"DOCSYNC_GITHUB_TOKEN is {state}"):
            _emit(f"docsync: {line}", token, err=True)
    parts, warnings = collect(args.repo)
    hosted, hosted_warnings = fetch(args.github_repo, args.offline, token, session)
    facts = ProjectFacts(hosted=hosted, warnings=(*warnings, *hosted_warnings), **parts)
    text = redact(render(facts), secrets=(token or "",))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(text.encode("utf-8"))
    for warning in facts.warnings:
        _emit(f"warning: {warning}", token, err=True)
    _emit(f"wrote {args.out.as_posix()}", token)
    return 0


def _fail(message: str) -> int:
    """Print one redacted ``docsync: error`` line on stderr and return exit code 2."""
    token = os.environ.get("DOCSYNC_GITHUB_TOKEN")
    _emit(f"docsync: error: {' '.join(message.split())}", token, err=True)
    return 2


def main(argv: Sequence[str] | None = None, session: HttpSession | None = None) -> int:
    """Console entry point; returns exit code 0, 1 or 2 and never a traceback.

    ``session`` is a test seam. ``--help`` is the only ``SystemExit`` source besides usage errors.
    """
    verbose = False
    try:
        args = parse_args(argv)
        verbose = args.verbose
        if args.command == "generate":
            return _generate(args, session)
        # TEMPORARY loud guard: removed by T16 (check); must not survive step 5.
        raise NotImplementedError("check is implemented in task T16")
    except KeyboardInterrupt:
        return _fail("interrupted")
    except BrokenPipeError:
        return _fail("output pipe closed")
    except DocsyncError as exc:
        return _fail(str(exc))
    except OSError as exc:
        return _fail(f"I/O error: {exc}")
    except Exception as exc:  # noqa: BLE001  mandated catch-all: exit 2, no traceback (FR-19)
        detail = f" ({type(exc).__name__})" if verbose else ""
        return _fail(f"unexpected internal error{detail}")
