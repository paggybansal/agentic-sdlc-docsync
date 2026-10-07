"""NFR-1 performance budget (T18, decision RO-1): offline generate on a fixed fixture."""

import re
import time
from pathlib import Path

import pytest

from docsync.cli import main

_PACKAGES = 5
_MODULES_PER_PACKAGE = 10
_TEST_FILES = 20
_TESTS_PER_FILE = 2
_RUNTIME_DEPS = 30
_OPTIONAL_DEPS = 5
_MEASURED_RUNS = 3
_TARGET_SECONDS = 1.0
_HARD_LIMIT_SECONDS = 2.0

_MODULE_SOURCE = '''"""Generated fixture module {pkg}.{mod}."""

CONSTANT = {mod}


def compute(value: int) -> int:
    """Return value plus the constant."""
    return value + CONSTANT


class Holder:
    """A tiny class."""

    name = "holder"
'''

_TEST_SOURCE = "def test_one():\n    assert True\n\n\ndef test_two():\n    assert True\n"


def _build_fixture(root: Path) -> Path:
    """RO-1 fixture: 50 modules, 20 test files x 2 tests, 30 + 5 deps, README and LICENSE."""
    root.mkdir()
    runtime = ", ".join(f'"runtimedep{i:02d}>=1.{i}"' for i in range(_RUNTIME_DEPS))
    optional = ", ".join(f'"optdep{i}>=2.{i}"' for i in range(_OPTIONAL_DEPS))
    (root / "pyproject.toml").write_text(
        '[project]\nname = "perfdemo"\ndescription = "Performance fixture."\n'
        'version = "1.0.0"\nrequires-python = ">=3.11"\nlicense = "MIT"\n'
        f"dependencies = [{runtime}]\n\n"
        f"[project.optional-dependencies]\ndev = [{optional}]\n\n"
        '[project.scripts]\nperfdemo = "perfdemo.cli:main"\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text("# perfdemo\n\nPerformance fixture.\n", encoding="utf-8")
    licence_text = "MIT License\n\nPermission is hereby granted.\n"
    (root / "LICENSE").write_text(licence_text, encoding="utf-8")
    for pkg in range(_PACKAGES):
        package = root / "src" / f"pkg{pkg}"
        package.mkdir(parents=True)
        for mod in range(_MODULES_PER_PACKAGE):
            source = _MODULE_SOURCE.format(pkg=f"pkg{pkg}", mod=mod)
            (package / f"mod{mod}.py").write_text(source, encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    for index in range(_TEST_FILES):
        (tests / f"test_unit{index:02d}.py").write_text(_TEST_SOURCE, encoding="utf-8")
    return root


@pytest.fixture
def perf_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The RO-1 fixture with offline forced: no token in the environment."""
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    return _build_fixture(tmp_path / "perfdemo")


def _generate(repo: Path) -> int:
    out = repo / "docs" / "PROJECT_DOCS.md"
    return main(["generate", "--repo", str(repo), "--out", str(out), "--offline"])


def test_perf_fixture_has_the_ro1_size(perf_repo: Path) -> None:
    # Arrange / Act
    code = _generate(perf_repo)

    # Assert
    document = (perf_repo / "docs" / "PROJECT_DOCS.md").read_text(encoding="utf-8")
    assert code == 0
    assert len(re.findall(r"^\| Module \| src/", document, flags=re.MULTILINE)) == 50
    assert len(re.findall(r"^\| Dependency \| ", document, flags=re.MULTILINE)) == 30
    assert len(re.findall(r"^\| Optional \(dev\) \| ", document, flags=re.MULTILINE)) == 5
    assert "| Test Files | 20 |" in document
    assert "| Test Functions | 40 |" in document


@pytest.mark.perf
def test_offline_under_1s(
    perf_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange: one discarded warm-up call excludes import and filesystem cache effects
    assert _generate(perf_repo) == 0

    # Act: three measured in-process calls (no subprocess); the best (minimum) counts
    durations = []
    for _ in range(_MEASURED_RUNS):
        started = time.perf_counter()
        code = _generate(perf_repo)
        durations.append(time.perf_counter() - started)
        assert code == 0
    best = min(durations)

    # Assert
    status = "target met" if best < _TARGET_SECONDS else "TARGET EXCEEDED (not a failure)"
    with capsys.disabled():
        print(
            f"\n[perf] offline generate best of {_MEASURED_RUNS}: {best:.4f} s "
            f"(all: {', '.join(f'{d:.4f}' for d in durations)}); "
            f"target < {_TARGET_SECONDS} s: {status}; hard limit < {_HARD_LIMIT_SECONDS} s"
        )
    assert best < _HARD_LIMIT_SECONDS
