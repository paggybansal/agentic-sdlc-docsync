"""Renderer: pure ``ProjectFacts`` to Markdown; never fetches or collects (FR-2, FR-3)."""

import re

from docsync import __version__
from docsync.model import NOT_FOUND, SCHEMA_VERSION, FieldValue, ProjectFacts


def normalise(value: FieldValue) -> str:
    """Make ``value`` safe for one table cell.

    Newlines, CR and whitespace runs collapse to one space, ``|`` is escaped, tuples are
    joined with ``", "``; anything empty after that is ``Not Found``.
    """
    items = (value,) if isinstance(value, str) else value
    cleaned = [re.sub(r"\s+", " ", item).strip().replace("|", "\\|") for item in items]
    return ", ".join(c for c in cleaned if c) or NOT_FOUND


def _section(title: str, rows: list[tuple[str, FieldValue]]) -> str:
    lines = [f"## {title}", "", "| Field | Value |", "|---|---|"]
    lines.extend(f"| {label} | {normalise(value)} |" for label, value in rows)
    return "\n".join(lines)


def render_overview(facts: ProjectFacts) -> str:
    """Section 1: Project Overview."""
    rows = [("Name", facts.overview.get("name", NOT_FOUND))]
    rows.append(("Description", facts.overview.get("description", NOT_FOUND)))
    return _section("Project Overview", rows)


def render_identity(facts: ProjectFacts) -> str:
    """Section 2: Identity & Metadata."""
    labels = (
        ("Version", "version"),
        ("Requires Python", "requires_python"),
        ("License", "license"),
        ("Authors", "authors"),
    )
    rows = [(title, facts.identity.get(key, NOT_FOUND)) for title, key in labels]
    return _section("Identity & Metadata", rows)


def render_hosted(facts: ProjectFacts) -> str:
    """Section 3: Hosted Repository Metadata."""
    labels = (
        ("Full Name", "full_name"),
        ("Description", "description"),
        ("Default Branch", "default_branch"),
        ("Visibility", "visibility"),
        ("License", "license"),
        ("Topics", "topics"),
    )
    return _section(
        "Hosted Repository Metadata", [(t, facts.hosted.get(k, NOT_FOUND)) for t, k in labels]
    )


def render_generation_info() -> str:
    """Section 7: Generation Info (tool and schema version only, FR-5)."""
    return _section(
        "Generation Info", [("Tool Version", __version__), ("Schema Version", SCHEMA_VERSION)]
    )
