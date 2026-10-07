"""Tests for docsync.collect (T5: pyproject.toml reading)."""

from pathlib import Path

import pytest

from docsync.collect import collect_pyproject
from docsync.model import NOT_FOUND

_FULL = """
[project]
name = "demo"
description = "A demo."
version = "1.2.3"
requires-python = ">=3.11"
license = "MIT"
authors = [{name = "Zed", email = "z@example.com"}, {name = "Amy"}]
dependencies = ["zlib-x>=1", "requests>=2"]

[project.optional-dependencies]
test = ["pytest", "coverage"]
dev = ["ruff"]

[project.scripts]
zeta = "demo.z:main"
alpha = "demo.a:main"
"""


def _write(repo: Path, content: str) -> None:
    (repo / "pyproject.toml").write_text(content, encoding="utf-8")


def test_collect_pyproject_full_file_reads_overview_and_identity(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, _FULL)

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.overview == {"name": "demo", "description": "A demo."}
    assert facts.identity == {
        "version": "1.2.3",
        "requires_python": ">=3.11",
        "license": "MIT",
        "authors": ("Zed", "Amy"),
    }
    assert facts.warnings == ()


def test_collect_pyproject_dependencies_sorted_by_code_point(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, _FULL)

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.dependencies == ("requests>=2", "zlib-x>=1")


def test_collect_pyproject_optional_groups_and_members_sorted(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, _FULL)

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert list(facts.optional_dependencies.items()) == [
        ("dev", ("ruff",)),
        ("test", ("coverage", "pytest")),
    ]


def test_collect_pyproject_entry_points_sorted(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, _FULL)

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.entry_points == ("alpha = demo.a:main", "zeta = demo.z:main")


def test_ec_7_missing_pyproject_is_not_found_without_warning(tmp_path: Path) -> None:
    # Arrange: empty repo

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.overview == {"name": NOT_FOUND, "description": NOT_FOUND}
    assert facts.identity["authors"] == NOT_FOUND
    assert facts.dependencies == ()
    assert facts.warnings == ()


def test_ec_13_malformed_toml_gives_not_found_and_one_warning(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, "[project\nname = ")

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.overview["name"] == NOT_FOUND
    assert len(facts.warnings) == 1


def test_ec_8_unreadable_pyproject_gives_one_warning(tmp_path: Path) -> None:
    # Arrange: a directory named pyproject.toml raises OSError on read
    (tmp_path / "pyproject.toml").mkdir()

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.overview["name"] == NOT_FOUND
    assert len(facts.warnings) == 1


def test_ec_8_undecodable_pyproject_gives_one_warning(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "pyproject.toml").write_bytes(b"\xff\xfe\x00bad")

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert len(facts.warnings) == 1


def test_collect_pyproject_warning_does_not_echo_file_content(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, "password = [unterminated")

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert "password" not in facts.warnings[0]


@pytest.mark.parametrize(
    ("license_toml", "expected"),
    [
        ('license = {text = "Apache-2.0"}', "Apache-2.0"),
        ('license = {file = "LICENSE"}', NOT_FOUND),
        ("license = 5", NOT_FOUND),
    ],
)
def test_collect_pyproject_license_forms(tmp_path: Path, license_toml: str, expected: str) -> None:
    # Arrange
    _write(tmp_path, f'[project]\nname = "d"\n{license_toml}\n')

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.identity["license"] == expected


def test_collect_pyproject_wrong_types_give_not_found(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, '[project]\nname = 3\ndependencies = "x"\nauthors = ["a"]\n')

    # Act
    facts = collect_pyproject(tmp_path)

    # Assert
    assert facts.overview["name"] == NOT_FOUND
    assert facts.dependencies == ()
    assert facts.identity["authors"] == NOT_FOUND


def test_collect_pyproject_opens_only_pyproject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    _write(tmp_path, _FULL)
    (tmp_path / ".env").write_text("X=1", encoding="utf-8")
    opened: list[str] = []
    original = Path.read_text

    def spy(self: Path, *args: object, **kwargs: object) -> str:
        opened.append(self.name)
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", spy)

    # Act
    collect_pyproject(tmp_path)

    # Assert
    assert opened == ["pyproject.toml"]
