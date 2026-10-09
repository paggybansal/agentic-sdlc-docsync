"""Tests for docsync.collect (T5: pyproject.toml reading)."""

import builtins
import os
import tempfile
from pathlib import Path

import pytest

from docsync.collect import collect, collect_pyproject, scan_modules
from docsync.model import NOT_FOUND, ProjectFacts


def _symlinks_available() -> bool:
    """Probe whether this environment may create directory symlinks."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.symlink(tmp, os.path.join(tmp, "probe"), target_is_directory=True)
        except (OSError, NotImplementedError):
            return False
    return True


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


def _touch(repo: Path, *relative: str) -> None:
    for rel in relative:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def test_scan_modules_prefers_src_over_repo_root(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "src/pkg/a.py", "stray.py")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("src/pkg/a.py",)


def test_scan_modules_without_src_uses_repo_root(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "pkg/b.py", "top.py", "notes.txt")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("pkg/b.py", "top.py")


@pytest.mark.parametrize(
    "skipped",
    [
        ".git", ".hidden", "tests", "test", "__pycache__", "venv", "env", "build", "dist",
        "node_modules", "site-packages", "demo.egg-info",
    ],
)
def test_scan_modules_skip_list_directory_is_excluded(tmp_path: Path, skipped: str) -> None:
    # Arrange
    _touch(tmp_path, f"{skipped}/x.py", "keep/y.py")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("keep/y.py",)


def test_scan_modules_skip_list_applies_inside_src(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "src/pkg/__pycache__/c.py", "src/pkg/d.py")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("src/pkg/d.py",)


@pytest.mark.skipif(
    not _symlinks_available(),
    reason=(
        "EL-1: directory symlink creation is not permitted in this environment "
        "(Windows needs elevated privileges or Developer Mode); "
        "see docs/04-impl-plan.md section 10 Environment Limitations"
    ),
)
def test_scan_modules_symlinked_directory_is_not_followed(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "real/z.py")
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("real/z.py",)


def test_scan_modules_output_sorted_by_code_point(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "b.py", "Z.py", "a/z.py", "a.py")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("Z.py", "a.py", "a/z.py", "b.py")


def test_ec_6_scan_modules_empty_repo_gives_empty_tuple(tmp_path: Path) -> None:
    # Arrange: empty repo

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ()


def test_scan_modules_paths_are_posix_and_relative(tmp_path: Path) -> None:
    # Arrange
    _touch(tmp_path, "src/a/b/c.py")

    # Act
    modules = scan_modules(tmp_path)

    # Assert
    assert modules == ("src/a/b/c.py",)
    assert all("\\" not in m and not m.startswith("/") for m in modules)


def _write_test(repo: Path, name: str, source: str) -> None:
    path = repo / "tests" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_collect_counts_module_level_test_functions(tmp_path: Path) -> None:
    # Arrange
    source = "def test_one(): pass\ndef test_two(): pass\ndef helper(): pass\n"
    _write_test(tmp_path, "test_a.py", source)

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"] == {"test_files": "1", "test_functions": "2"}


def test_collect_counts_methods_of_any_class(tmp_path: Path) -> None:
    # Arrange
    source = (
        "class TestA:\n    def test_m(self): pass\n    def other(self): pass\n"
        "class B:\n    def test_n(self): pass\n"
    )
    _write_test(tmp_path, "test_a.py", source)

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"]["test_functions"] == "2"


def test_collect_counts_async_test_functions(tmp_path: Path) -> None:
    # Arrange
    source = "async def test_a(): pass\nclass T:\n    async def test_b(self): pass\n"
    _write_test(tmp_path, "test_a.py", source)

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"]["test_functions"] == "2"


def test_collect_ignores_functions_nested_inside_functions(tmp_path: Path) -> None:
    # Arrange
    _write_test(tmp_path, "test_a.py", "def test_a():\n    def test_inner(): pass\n")

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"]["test_functions"] == "1"


def test_collect_only_test_prefixed_py_files_are_counted(tmp_path: Path) -> None:
    # Arrange
    _write_test(tmp_path, "test_a.py", "def test_a(): pass\n")
    _write_test(tmp_path, "conftest.py", "def test_b(): pass\n")
    _write_test(tmp_path, "sub/test_c.py", "def test_c(): pass\n")

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"] == {"test_files": "2", "test_functions": "2"}


def test_ec_8_syntax_error_test_file_is_counted_with_one_warning(tmp_path: Path) -> None:
    # Arrange
    _write_test(tmp_path, "test_bad.py", "def test_x(:\n")
    _write_test(tmp_path, "test_ok.py", "def test_y(): pass\n")

    # Act
    parts, warnings = collect(tmp_path)

    # Assert
    assert parts["tests"] == {"test_files": "2", "test_functions": "1"}
    assert len(warnings) == 1
    assert "tests/test_bad.py" in warnings[0]


def test_ec_8_undecodable_test_file_is_counted_with_one_warning(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_bin.py").write_bytes(b"\xff\xfe\x00")

    # Act
    parts, warnings = collect(tmp_path)

    # Assert
    assert parts["tests"] == {"test_files": "1", "test_functions": "0"}
    assert len(warnings) == 1


def test_collect_tests_dir_without_tests_counts_zero(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "tests").mkdir()

    # Act
    parts, _ = collect(tmp_path)

    # Assert
    assert parts["tests"] == {"test_files": "0", "test_functions": "0"}


def test_collect_warnings_combine_pyproject_then_tests(tmp_path: Path) -> None:
    # Arrange
    _write(tmp_path, "[project")
    _write_test(tmp_path, "test_bad.py", "def (:\n")

    # Act
    _, warnings = collect(tmp_path)

    # Assert
    assert len(warnings) == 2
    assert warnings[0].startswith("pyproject.toml")


def test_ec_6_empty_repo_returns_complete_default_facts(tmp_path: Path) -> None:
    # Arrange: empty repo

    # Act
    parts, warnings = collect(tmp_path)

    # Assert
    assert set(parts) == {
        "overview", "identity", "modules", "entry_points",
        "dependencies", "optional_dependencies", "tests",
    }
    assert parts["overview"] == {"name": NOT_FOUND, "description": NOT_FOUND}
    assert parts["tests"] == {"test_files": NOT_FOUND, "test_functions": NOT_FOUND}
    assert parts["modules"] == ()
    assert warnings == ()


def test_collect_parts_build_a_project_facts(tmp_path: Path) -> None:
    # Arrange
    parts, warnings = collect(tmp_path)

    # Act
    facts = ProjectFacts(hosted={}, warnings=warnings, **parts)

    # Assert
    assert facts.modules == ()


def test_dotenv_never_opened(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    _write(tmp_path, _FULL)
    _write_test(tmp_path, "test_a.py", "def test_a(): pass\n")
    (tmp_path / ".env").write_text("TOKEN=abc", encoding="utf-8")
    opened: list[str] = []
    real_open, real_read_text = builtins.open, Path.read_text

    def spy_open(file: object, *args: object, **kwargs: object) -> object:
        opened.append(Path(str(file)).name)
        return real_open(file, *args, **kwargs)  # type: ignore[call-overload]

    def spy_read_text(self: Path, *args: object, **kwargs: object) -> str:
        opened.append(self.name)
        return real_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(Path, "read_text", spy_read_text)

    # Act
    collect(tmp_path)

    # Assert
    assert ".env" not in opened
    assert "pyproject.toml" in opened
