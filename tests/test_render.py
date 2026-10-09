"""Tests for docsync.render (T11: normaliser, sections 1, 2, 3 and 7)."""

import re
from typing import Any

import pytest

from docsync import __version__
from docsync.model import NOT_FOUND, SCHEMA_VERSION, ProjectFacts
from docsync.render import (
    normalise,
    render,
    render_dependencies,
    render_generation_info,
    render_hosted,
    render_identity,
    render_modules,
    render_overview,
    render_tests,
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
        "modules": ("src/demo/a.py", "src/demo/b.py"),
        "entry_points": ("demo = demo.cli:main",),
        "dependencies": ("requests>=2",),
        "optional_dependencies": {"dev": ("pytest", "ruff"), "docs": ("mkdocs",)},
        "tests": {"test_files": "3", "test_functions": "12"},
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


_TITLES = [
    "Project Overview",
    "Identity & Metadata",
    "Hosted Repository Metadata",
    "Modules & Entry Points",
    "Dependencies",
    "Test Suite Summary",
    "Generation Info",
]


def _default_facts() -> ProjectFacts:
    """What the collectors and github.fetch return for an empty repo (EC-6)."""
    return ProjectFacts(
        overview=dict.fromkeys(("name", "description"), NOT_FOUND),
        identity=dict.fromkeys(("version", "requires_python", "license", "authors"), NOT_FOUND),
        hosted=dict.fromkeys(
            ("full_name", "description", "default_branch", "visibility", "license", "topics"),
            NOT_FOUND,
        ),
        modules=(),
        entry_points=(),
        dependencies=(),
        optional_dependencies={},
        tests=dict.fromkeys(("test_files", "test_functions"), NOT_FOUND),
        warnings=(),
    )


def test_document_has_seven_sections_in_order() -> None:
    # Arrange
    facts = _facts()

    # Act
    document = render(facts)

    # Assert
    assert re.findall(r"^## (.+)$", document, flags=re.MULTILINE) == _TITLES


def test_render_ends_with_exactly_one_newline() -> None:
    # Arrange / Act
    document = render(_facts())

    # Assert
    assert document.endswith("|\n")
    assert not document.endswith("\n\n")


def test_render_output_contains_no_carriage_return() -> None:
    # Arrange
    facts = _facts(overview={"name": "a\r\nb", "description": "c\rd"})

    # Act
    document = render(facts)

    # Assert
    assert "\r" not in document


def test_render_called_twice_gives_identical_string() -> None:
    # Arrange
    facts = _facts()

    # Act / Assert
    assert render(facts) == render(facts)


def test_ec_6_default_facts_render_a_full_seven_section_document() -> None:
    # Arrange
    facts = _default_facts()

    # Act
    document = render(facts)

    # Assert
    assert re.findall(r"^## (.+)$", document, flags=re.MULTILINE) == _TITLES
    assert "| Module | Not Found |" in document
    assert "| Entry Point | Not Found |" in document
    assert "| Dependency | Not Found |" in document
    assert "| Optional Dependency | Not Found |" in document
    assert "| Test Files | Not Found |" in document
    assert "| Test Functions | Not Found |" in document


def test_unresolved_fields_in_default_document_are_all_not_found_except_generation_info() -> None:
    # Arrange
    document = render(_default_facts())

    # Act
    rows = [ln for ln in document.splitlines() if ln.startswith("| ") and "Field |" not in ln]
    non_default = [r for r in rows if "Not Found" not in r]

    # Assert
    assert len(non_default) == 2
    assert all(r.startswith(("| Tool Version", "| Schema Version")) for r in non_default)


def test_render_modules_lists_modules_then_entry_points() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_modules(facts)

    # Assert
    assert text.splitlines()[0] == "## Modules & Entry Points"
    assert text.splitlines()[4:] == [
        "| Module | src/demo/a.py |",
        "| Module | src/demo/b.py |",
        "| Entry Point | demo = demo.cli:main |",
    ]


def test_render_modules_empty_collections_render_not_found() -> None:
    # Arrange
    facts = _facts(modules=(), entry_points=())

    # Act
    text = render_modules(facts)

    # Assert
    assert text.splitlines()[4:] == ["| Module | Not Found |", "| Entry Point | Not Found |"]


def test_render_modules_pipe_in_path_cannot_break_table() -> None:
    # Arrange
    facts = _facts(modules=("src/a|b.py",), entry_points=())

    # Act
    text = render_modules(facts)

    # Assert
    assert "| Module | src/a\\|b.py |" in text


def test_render_dependencies_lists_runtime_then_optional_groups() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_dependencies(facts)

    # Assert
    assert text.splitlines()[0] == "## Dependencies"
    assert text.splitlines()[4:] == [
        "| Dependency | requests>=2 |",
        "| Optional (dev) | pytest |",
        "| Optional (dev) | ruff |",
        "| Optional (docs) | mkdocs |",
    ]


def test_render_dependencies_empty_group_renders_not_found() -> None:
    # Arrange
    facts = _facts(dependencies=(), optional_dependencies={"dev": ()})

    # Act
    text = render_dependencies(facts)

    # Assert
    assert text.splitlines()[4:] == ["| Dependency | Not Found |", "| Optional (dev) | Not Found |"]


def test_render_tests_shows_static_counts() -> None:
    # Arrange
    facts = _facts()

    # Act
    text = render_tests(facts)

    # Assert
    assert text.splitlines()[0] == "## Test Suite Summary"
    assert text.splitlines()[4:] == ["| Test Files | 3 |", "| Test Functions | 12 |"]


def test_render_tests_missing_keys_render_not_found() -> None:
    # Arrange
    facts = _facts(tests={})

    # Act
    text = render_tests(facts)

    # Assert
    assert text.splitlines()[4:] == ["| Test Files | Not Found |", "| Test Functions | Not Found |"]
