"""Local collector: reads repository files statically, never opens dotfiles (FR-7)."""

import os
import tomllib
from pathlib import Path
from typing import Any, NamedTuple

from docsync.model import NOT_FOUND, FieldValue

_SKIP_DIRS = frozenset(
    {
        "tests", "test", "__pycache__", "venv", "env",
        "build", "dist", "node_modules", "site-packages",
    }
)


class PyprojectFacts(NamedTuple):
    """Facts taken from ``pyproject.toml`` plus any warnings raised while reading it."""

    overview: dict[str, FieldValue]
    identity: dict[str, FieldValue]
    dependencies: tuple[str, ...]
    optional_dependencies: dict[str, tuple[str, ...]]
    entry_points: tuple[str, ...]
    warnings: tuple[str, ...]


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else NOT_FOUND


def _strings(value: object) -> tuple[str, ...]:
    items = value if isinstance(value, list) else []
    return tuple(sorted(i for i in items if isinstance(i, str)))


def _table(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _license(value: object) -> str:
    return _text(_table(value).get("text") if isinstance(value, dict) else value)


def _authors(value: object) -> FieldValue:
    items = value if isinstance(value, list) else []
    names = tuple(_text(_table(a).get("name")) for a in items)
    names = tuple(n for n in names if n != NOT_FOUND)
    return names or NOT_FOUND


def collect_pyproject(repo: Path) -> PyprojectFacts:
    """Read ``<repo>/pyproject.toml`` into facts; failures degrade to ``Not Found``."""
    warnings: list[str] = []
    data: dict[str, Any] = {}
    try:
        data = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    except FileNotFoundError:
        pass
    except tomllib.TOMLDecodeError:
        warnings.append("pyproject.toml is not valid TOML; its fields are Not Found")
    except (OSError, UnicodeDecodeError):
        warnings.append("pyproject.toml could not be read; its fields are Not Found")
    project = _table(data.get("project"))
    optional = _table(project.get("optional-dependencies"))
    scripts = _table(project.get("scripts"))
    return PyprojectFacts(
        overview={
            "name": _text(project.get("name")),
            "description": _text(project.get("description")),
        },
        identity={
            "version": _text(project.get("version")),
            "requires_python": _text(project.get("requires-python")),
            "license": _license(project.get("license")),
            "authors": _authors(project.get("authors")),
        },
        dependencies=_strings(project.get("dependencies")),
        optional_dependencies={g: _strings(optional[g]) for g in sorted(optional)},
        entry_points=tuple(sorted(f"{k} = {v}" for k, v in scripts.items() if isinstance(v, str))),
        warnings=tuple(warnings),
    )


def _skipped(name: str) -> bool:
    return name.startswith(".") or name in _SKIP_DIRS or name.endswith(".egg-info")


def scan_modules(repo: Path) -> tuple[str, ...]:
    """List ``.py`` files as sorted POSIX paths relative to ``repo``.

    Scans ``src/`` when it is a real directory, else the repo root. Skip-listed and
    symlinked directories are not entered.
    """
    src = repo / "src"
    base = src if src.is_dir() and not src.is_symlink() else repo
    found: list[str] = []
    for root, dirs, files in os.walk(base, followlinks=False):
        dirs[:] = [d for d in dirs if not _skipped(d) and not (Path(root) / d).is_symlink()]
        found.extend(Path(root, f).relative_to(repo).as_posix() for f in files if f.endswith(".py"))
    return tuple(sorted(found))
