"""Tests for docsync.render (T11: normaliser, sections 1, 2, 3 and 7)."""

import re
from typing import Any

import pytest

from docsync import __version__
from docsync.model import NOT_FOUND, SCHEMA_VERSION, ProjectFacts
from docsync.render import (
    normalise,
    render_generation_info,
    render_hosted,
    render_identity,
    render_overview,
)


def _facts(**overrides: Any) -> ProjectFacts:
    base: dict[str, Any] = {
        "overview": {"name": "demo", "description": "A demo."},
        "identity": {
            "version": "1.2.3",
            "requires_python": ">=3.11",
            "license": "MIT",
            "authors": ("Amy", "Zed"),
        },
        "hosted": {
            "full_name": "octo/demo",
            "description": "Hosted demo.",
            "default_branch": "main",
            "visibility": "public",
            "license": "MIT",
            "topics": ("alpha", "zeta"),
        },
        "modules": (),
        "entry_points": (),
        "dependencies": (),
        "optional_dependencies": {},
        "tests": {},
        "warnings": (),
    }
    base.update(overrides)
    return ProjectFacts(**base)


def test_normalise_plain_string_is_unchanged() -> None:
    # Arrange / Act / Assert
    assert normalise("hello world") == "hello world"


@pytest.mark.parametrize("raw", ["a\nb", "a\r\nb", "a\rb", "a\n\n\r\n  b", "a \t b"])
def test_normalise_newlines_and_whitespace_collapse_to_one_space(raw: str) -> None:
    # Arrange / Act
    result = normalise(raw)

    # Assert
    assert result == "a b"


def test_normalise_pipe_is_escaped() -> None:
    # Arrange / Act / Assert
    assert normalise("a|b") == "a\\|b"


def test_normalise_surrounding_whitespace_is_stripped() -> None:
    # Arrange / Act / Assert
    assert normalise("  x  ") == "x"


@pytest.mark.parametrize("empty", ["", "   ", "\n\r\t", (), ("", " ")])
def test_normalise_empty_values_become_not_found(empty: Any) -> None:
    # Arrange / Act / Assert
    assert normalise(empty) == NOT_FOUND


def test_normalise_sentinel_is_preserved() -> None:
    # Arrange / Act / Assert
    assert normalise(NOT_FOUND) == "Not Found"


def test_normalise_tuple_is_joined_with_comma_space() -> None:
    # Arrange / Act / Assert
    assert normalise(("a", "b|c")) == "a, b\\|c"


def test_render_overview_has_heading_and_rows() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_overview(facts)

    # Assert
    assert text == (
        "## Project Overview\n\n| Field | Value |\n|---|---|\n"
        "| Name | demo |\n| Description | A demo. |"
    )


def test_render_identity_has_heading_and_four_rows() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_identity(facts)

    # Assert
    assert text.splitlines()[0] == "## Identity & Metadata"
    assert "| Version | 1.2.3 |" in text
    assert "| Requires Python | >=3.11 |" in text
    assert "| License | MIT |" in text
    assert "| Authors | Amy, Zed |" in text


def test_render_hosted_has_heading_and_six_rows() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_hosted(facts)

    # Assert
    assert text.splitlines()[0] == "## Hosted Repository Metadata"
    assert len(text.splitlines()) == 4 + 6
    assert "| Topics | alpha, zeta |" in text
    assert "| Default Branch | main |" in text


def test_unresolved_fields_render_not_found() -> None:
    # Arrange
    facts = _facts(
        overview={"name": NOT_FOUND, "description": NOT_FOUND},
        identity={"version": NOT_FOUND, "authors": NOT_FOUND},
        hosted=dict.fromkeys(("full_name", "topics"), NOT_FOUND),
    )

    # Act
    text = "\n".join([render_overview(facts), render_identity(facts), render_hosted(facts)])

    # Assert
    assert "| Name | Not Found |" in text
    assert "| Version | Not Found |" in text
    assert "| Authors | Not Found |" in text
    assert "| Topics | Not Found |" in text


def test_missing_dict_keys_render_not_found() -> None:
    # Arrange
    facts = _facts(overview={}, identity={}, hosted={})

    # Act
    text = "\n".join([render_overview(facts), render_identity(facts), render_hosted(facts)])

    # Assert
    rows = [line for line in text.splitlines() if line.startswith("| ") and "Field" not in line]
    assert len(rows) == 2 + 4 + 6
    assert all(row.endswith("| Not Found |") for row in rows)


def test_hostile_description_cannot_alter_structure() -> None:
    # Arrange
    facts = _facts(overview={"name": "demo", "description": "a\r\nb|c\rd\n## Fake\n| x |"})

    # Act
    text = render_overview(facts)

    # Assert
    assert "\r" not in text
    assert len(text.splitlines()) == 4 + 2
    assert text.splitlines()[5] == "| Description | a b\\|c d ## Fake \\| x \\| |"


def test_generation_info_contains_only_tool_and_schema_version() -> None:
    # Arrange / Act
    text = render_generation_info()

    # Assert
    assert text == (
        "## Generation Info\n\n| Field | Value |\n|---|---|\n"
        f"| Tool Version | {__version__} |\n| Schema Version | {SCHEMA_VERSION} |"
    )


def test_generation_info_has_no_volatile_values() -> None:
    # Arrange / Act
    text = render_generation_info()

    # Assert
    assert not re.search(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}", text)
    assert not re.search(r"\b[0-9a-f]{7,40}\b", text)
    assert "commit" not in text.lower()


def test_sections_render_identically_twice() -> None:
    # Arrange
    facts = _facts()

    # Act / Assert
    assert render_hosted(facts) == render_hosted(facts)
