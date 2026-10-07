"""End-to-end tests through ``cli.main`` and ``python -m docsync`` (T17; no production code)."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from docsync.cli import main

_PYPROJECT = """\
[project]
name = "shop"
description = "Order service | v2"
version = "2.1.0"
requires-python = ">=3.11"
license = "MIT"
authors = [{name = "Zed"}, {name = "Amy"}]
dependencies = ["requests>=2.32", "attrs>=23"]

[project.optional-dependencies]
dev = ["pytest", "ruff"]

[project.scripts]
shop = "shop.cli:main"
"""

_FILES = {
    "src/shop/__init__.py": "",
    "src/shop/orders.py": "def place(): pass\n",
    "src/shop/zeta.py": "",
    "src/shop/sub/deep.py": "",
    "src/shop/__pycache__/cached.py": "",
    "src/shop/build/generated.py": "",
    ".git/hooks/pre-commit.py": "",
    "tests/test_orders.py": (
        "def test_a(): pass\ndef test_b(): pass\nclass TestC:\n    def test_c(self): pass\n"
    ),
    "tests/test_zeta.py": "async def test_d(): pass\n",
    "tests/helpers.py": "def test_not_counted(): pass\n",
}


def _build(root: Path, order: list[str] | None = None) -> Path:
    """Create the realistic fixture repo at ``root``; ``order`` varies creation order."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    for rel in order or list(_FILES):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_FILES[rel], encoding="utf-8")
    return root


@pytest.fixture
def shop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The realistic repo, used as the cwd, with no token in the environment."""
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    root = _build(tmp_path / "shop")
    monkeypatch.chdir(root)
    return root


def _document(root: Path) -> bytes:
    return (root / "docs" / "PROJECT_DOCS.md").read_bytes()


def test_generate_twice_is_byte_identical(shop: Path) -> None:
    # Arrange
    assert main(["generate", "--offline"]) == 0
    first = _document(shop)

    # Act
    assert main(["generate", "--offline"]) == 0
    second = _document(shop)

    # Assert
    assert first == second
    assert sum(a != b for a, b in zip(first, second, strict=True)) == 0


def test_generate_twice_via_python_dash_m_is_byte_identical(tmp_path: Path) -> None:
    # Arrange
    root = _build(tmp_path / "shop")
    src = Path(__file__).resolve().parents[1] / "src"
    env = {**os.environ, "PYTHONPATH": str(src)}
    env.pop("DOCSYNC_GITHUB_TOKEN", None)
    run = [sys.executable, "-m", "docsync", "generate", "--offline"]

    # Act
    first = subprocess.run(run, cwd=root, env=env, capture_output=True, check=False)
    first_bytes = _document(root)
    second = subprocess.run(run, cwd=root, env=env, capture_output=True, check=False)

    # Assert
    assert (first.returncode, second.returncode) == (0, 0)
    assert _document(root) == first_bytes


def test_document_does_not_depend_on_file_creation_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    forward = _build(tmp_path / "forward", list(_FILES))
    backward = _build(tmp_path / "backward", list(reversed(list(_FILES))))

    # Act
    for root in (forward, backward):
        monkeypatch.chdir(root)
        assert main(["generate", "--offline"]) == 0

    # Assert
    assert _document(forward) == _document(backward)


def test_generate_then_check_returns_0(shop: Path) -> None:
    # Arrange
    assert main(["generate", "--offline"]) == 0

    # Act
    code = main(["check", "--offline"])

    # Assert
    assert code == 0


def test_generate_then_check_fails_after_a_repo_change(shop: Path) -> None:
    # Arrange
    assert main(["generate", "--offline"]) == 0
    (shop / "src" / "shop" / "added.py").write_text("", encoding="utf-8")

    # Act
    code = main(["check", "--offline"])

    # Assert
    assert code == 1


def test_realistic_fixture_renders_every_section_with_expected_rows(shop: Path) -> None:
    # Arrange
    main(["generate", "--offline"])

    # Act
    document = _document(shop).decode("utf-8")

    # Assert
    assert re.findall(r"^## (.+)$", document, flags=re.MULTILINE) == [
        "Project Overview",
        "Identity & Metadata",
        "Hosted Repository Metadata",
        "Modules & Entry Points",
        "Dependencies",
        "Test Suite Summary",
        "Generation Info",
    ]
    for row in (
        "| Name | shop |",
        "| Description | Order service \\| v2 |",
        "| Version | 2.1.0 |",
        "| Requires Python | >=3.11 |",
        "| License | MIT |",
        "| Authors | Zed, Amy |",
        "| Full Name | Not Found |",
        "| Entry Point | shop = shop.cli:main |",
        "| Test Files | 2 |",
        "| Test Functions | 4 |",
    ):
        assert row in document


def test_realistic_fixture_lists_modules_and_dependencies_sorted_without_skipped_dirs(
    shop: Path,
) -> None:
    # Arrange
    main(["generate", "--offline"])

    # Act
    rows = [ln for ln in _document(shop).decode("utf-8").splitlines() if ln.startswith("| ")]

    # Assert
    assert [r for r in rows if r.startswith("| Module")] == [
        "| Module | src/shop/__init__.py |",
        "| Module | src/shop/orders.py |",
        "| Module | src/shop/sub/deep.py |",
        "| Module | src/shop/zeta.py |",
    ]
    assert [r for r in rows if r.startswith(("| Dependency", "| Optional"))] == [
        "| Dependency | attrs>=23 |",
        "| Dependency | requests>=2.32 |",
        "| Optional (dev) | pytest |",
        "| Optional (dev) | ruff |",
    ]


def test_output_contains_no_absolute_paths_or_backslash_separators(shop: Path) -> None:
    # Arrange
    main(["generate", "--offline"])

    # Act
    document = _document(shop).decode("utf-8")

    # Assert
    assert str(shop) not in document
    assert shop.as_posix() not in document
    assert "\\" not in document.replace("\\|", "")
    assert not re.search(r"\b[A-Za-z]:[\\/]", document)


def test_empty_repo_produces_full_document(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    # Act
    code = main(["generate"])

    # Assert
    document = _document(tmp_path).decode("utf-8")
    assert code == 0
    assert len(re.findall(r"^## ", document, flags=re.MULTILINE)) == 7
    assert "| Name | Not Found |" in document
    assert "| Module | Not Found |" in document
    assert "| Test Files | Not Found |" in document
    assert document.endswith("\n") and not document.endswith("\n\n")


def test_empty_repo_generate_then_check_returns_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["generate"]) == 0

    # Act
    code = main(["check"])

    # Assert
    assert code == 0


def test_crlf_windows_style_pyproject_cannot_break_the_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: a pyproject saved with Windows CRLF line endings and a hostile description
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    raw = '[project]\r\nname = "win"\r\ndescription = "line one\\r\\nline | two\\n## Fake"\r\n'
    (tmp_path / "pyproject.toml").write_bytes(raw.encode("utf-8"))

    # Act
    code = main(["generate"])

    # Assert
    data = _document(tmp_path)
    document = data.decode("utf-8")
    assert code == 0
    assert b"\r" not in data
    assert "| Description | line one line \\| two ## Fake |" in document
    assert len(re.findall(r"^## ", document, flags=re.MULTILINE)) == 7


def test_crlf_sources_and_tests_are_counted_correctly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    source = b"def test_a():\r\n    pass\r\n\r\ndef test_b():\r\n    pass\r\n"
    (tmp_path / "tests" / "test_w.py").write_bytes(source)

    # Act
    code = main(["generate"])

    # Assert
    document = _document(tmp_path).decode("utf-8")
    assert code == 0
    assert "| Test Functions | 2 |" in document
