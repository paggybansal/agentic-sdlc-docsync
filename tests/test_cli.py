"""Tests for docsync.cli (T13-T16: parsing, generate, error handling, check)."""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from docsync.cli import CliArgs, main, parse_args
from docsync.errors import CollectError, UsageError

_TOKEN_SHAPED = "ghp_A1b2C3d4E5f6G7h8I9j0K1"


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every CLI test with the cwd in tmp_path, so none depends on or writes to the repo."""
    monkeypatch.chdir(tmp_path)


def _assert_one_line_error(capsys: pytest.CaptureFixture[str]) -> str:
    err = capsys.readouterr().err
    assert len(err.strip().splitlines()) == 1
    assert "Traceback" not in err
    return err


def test_flags_and_defaults() -> None:
    # Arrange / Act
    args = parse_args(["generate"])

    # Assert
    assert args == CliArgs(
        command="generate",
        repo=Path("."),
        out=Path("docs/PROJECT_DOCS.md"),
        github_repo=None,
        offline=False,
        verbose=False,
    )


def test_all_flags_are_parsed_for_generate(tmp_path: Path) -> None:
    # Arrange
    argv = [
        "generate", "--repo", str(tmp_path), "--out", "x/out.md",
        "--github-repo", "octo/demo", "--offline", "--verbose",
    ]

    # Act
    args = parse_args(argv)

    # Assert
    assert args == CliArgs("generate", tmp_path, Path("x/out.md"), "octo/demo", True, True)


def test_check_subcommand_accepts_the_same_flags(tmp_path: Path) -> None:
    # Arrange / Act
    args = parse_args(["check", "--repo", str(tmp_path), "--offline"])

    # Assert
    assert args.command == "check"
    assert args.offline is True


def test_missing_subcommand_exits_2_with_one_line(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main([])

    # Assert
    assert code == 2
    _assert_one_line_error(capsys)


def test_unknown_subcommand_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main(["frobnicate"])

    # Assert
    assert code == 2
    _assert_one_line_error(capsys)


def test_unknown_flag_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main(["generate", "--nope"])

    # Assert
    assert code == 2
    _assert_one_line_error(capsys)


def test_ec_10_nonexistent_repo_exits_2_with_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    missing = tmp_path / "does-not-exist"

    # Act
    code = main(["generate", "--repo", str(missing)])

    # Assert
    assert code == 2
    assert "--repo" in _assert_one_line_error(capsys)


def test_ec_10_file_as_repo_exits_2_with_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    a_file = tmp_path / "file.txt"
    a_file.write_text("x", encoding="utf-8")

    # Act
    code = main(["check", "--repo", str(a_file)])

    # Assert
    assert code == 2
    assert "--repo" in _assert_one_line_error(capsys)


@pytest.mark.parametrize(
    "value",
    [
        "a", "a/b/c", "../x", "./.", "o/..", "../..", "/n", "o/", "",
        "o/n?x=1", "o/n x", "o/n\n", "o/n#f",
    ],
    ids=repr,
)
def test_ec_11_invalid_github_repo_is_rejected(value: str) -> None:
    # Arrange / Act / Assert
    with pytest.raises(UsageError, match="OWNER/NAME"):
        parse_args(["generate", "--github-repo", value])


@pytest.mark.parametrize("value", ["octo/demo", "a.b/c-d_e", "o/.hidden", "..a/b", "o/b.."])
def test_ec_11_valid_github_repo_is_accepted(value: str) -> None:
    # Arrange / Act
    args = parse_args(["check", "--github-repo", value])

    # Assert
    assert args.github_repo == value


def test_ec_11_invalid_github_repo_exits_2_with_one_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange / Act
    code = main(["generate", "--github-repo", "../x"])

    # Assert
    assert code == 2
    assert "--github-repo" in _assert_one_line_error(capsys)


def test_usage_error_message_echoing_a_token_is_redacted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange / Act
    code = main(["generate", "--github-repo", _TOKEN_SHAPED])

    # Assert
    err = _assert_one_line_error(capsys)
    assert code == 2
    assert _TOKEN_SHAPED not in err
    assert "[REDACTED]" in err


def test_argparse_error_echoing_a_token_is_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main([_TOKEN_SHAPED])

    # Assert
    err = _assert_one_line_error(capsys)
    assert code == 2
    assert _TOKEN_SHAPED not in err


def test_help_lists_both_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    with pytest.raises(SystemExit) as info:
        main(["--help"])

    # Assert
    out = capsys.readouterr().out
    assert info.value.code == 0
    assert "generate" in out
    assert "check" in out


def test_generate_help_lists_all_flags(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    with pytest.raises(SystemExit) as info:
        main(["generate", "--help"])

    # Assert
    out = capsys.readouterr().out
    assert info.value.code == 0
    for flag in ("--repo", "--out", "--github-repo", "--offline", "--verbose"):
        assert flag in out


_PYPROJECT = '[project]\nname = "demo"\ndescription = "A demo."\nversion = "1.0.0"\n'
_SECRET_ENV = "tok-SECRET-value-123"
_PAYLOAD = {"full_name": "octo/demo", "default_branch": "main", "topics": ["b", "a"]}


class _Response:
    def __init__(self, status_code: int = 200, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class _Session:
    """Fake HTTP session: records calls, returns a canned response."""

    def __init__(self, response: _Response | None = None) -> None:
        self.calls: list[str] = []
        self._response = response or _Response(404)

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> _Response:
        self.calls.append(url)
        return self._response


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tiny repo that is also the cwd, with no token in the environment."""
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)
    return tmp_path


def test_generate_writes_default_output(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main(["generate"])

    # Assert
    document = (repo / "docs" / "PROJECT_DOCS.md").read_text(encoding="utf-8")
    assert code == 0
    assert capsys.readouterr().out == "wrote docs/PROJECT_DOCS.md\n"
    assert document.startswith("## Project Overview")
    assert "| Name | demo |" in document


def test_generate_creates_missing_parent_directories(repo: Path) -> None:
    # Arrange / Act
    code = main(["generate", "--out", "deep/er/out.md"])

    # Assert
    assert code == 0
    assert (repo / "deep" / "er" / "out.md").is_file()


def test_generate_written_bytes_are_utf8_lf(repo: Path) -> None:
    # Arrange
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "d"\ndescription = "café\\r\\nbar"\n', encoding="utf-8"
    )

    # Act
    main(["generate"])

    # Assert
    data = (repo / "docs" / "PROJECT_DOCS.md").read_bytes()
    assert b"\r" not in data
    assert "café bar".encode() in data
    assert data.endswith(b"|\n")


def test_relative_out_is_resolved_against_cwd_not_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    target = tmp_path / "repo"
    target.mkdir()
    (target / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    cwd = target / "sub"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)

    # Act
    code = main(["generate", "--repo", str(target), "--out", "o.md"])

    # Assert
    assert code == 0
    assert (cwd / "o.md").is_file()
    assert not (target / "o.md").exists()


def test_offline_flag_makes_no_requests(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    session = _Session()

    # Act
    code = main(["generate", "--github-repo", "octo/demo", "--offline"], session)

    # Assert
    assert code == 0
    assert session.calls == []


def test_ec_5_generate_without_token_makes_no_requests(repo: Path) -> None:
    # Arrange
    session = _Session()

    # Act
    code = main(["generate", "--github-repo", "octo/demo"], session)

    # Assert
    assert code == 0
    assert session.calls == []
    assert "| Full Name | Not Found |" in (repo / "docs/PROJECT_DOCS.md").read_text("utf-8")


def test_ec_14_generate_without_github_repo_makes_no_requests(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    session = _Session()

    # Act
    code = main(["generate"], session)

    # Assert
    assert code == 0
    assert session.calls == []


def test_generate_online_renders_hosted_fields(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    session = _Session(_Response(200, _PAYLOAD))

    # Act
    code = main(["generate", "--github-repo", "octo/demo"], session)

    # Assert
    document = (repo / "docs/PROJECT_DOCS.md").read_text("utf-8")
    assert code == 0
    assert session.calls == ["https://api.github.com/repos/octo/demo"]
    assert "| Full Name | octo/demo |" in document
    assert "| Topics | a, b |" in document


def test_generate_api_failure_warns_on_stderr_and_exits_0(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)

    # Act
    code = main(["generate", "--github-repo", "octo/demo"], _Session(_Response(404)))

    # Assert
    captured = capsys.readouterr()
    assert code == 0
    assert "warning: GitHub lookup failed" in captured.err
    assert captured.out == "wrote docs/PROJECT_DOCS.md\n"


def test_collect_warnings_go_to_stderr_not_stdout(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    (repo / "pyproject.toml").write_text("[project", encoding="utf-8")

    # Act
    code = main(["generate"])

    # Assert
    captured = capsys.readouterr()
    assert code == 0
    assert "warning: pyproject.toml is not valid TOML" in captured.err
    assert "warning" not in captured.out


def test_token_value_never_in_output_or_file(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)

    # Act
    main(["generate", "--github-repo", "octo/demo", "--verbose"], _Session(_Response(403)))

    # Assert
    captured = capsys.readouterr()
    assert _SECRET_ENV not in captured.out + captured.err
    assert _SECRET_ENV not in (repo / "docs/PROJECT_DOCS.md").read_text("utf-8")
    assert "docsync: DOCSYNC_GITHUB_TOKEN is set" in captured.err


def test_verbose_reports_token_not_set(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    main(["generate", "--verbose"])

    # Assert
    assert "docsync: DOCSYNC_GITHUB_TOKEN is not set" in capsys.readouterr().err


def test_without_verbose_no_diagnostics_are_printed(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange / Act
    main(["generate"])

    # Assert
    assert capsys.readouterr().err == ""


def test_redaction_applied_to_file_and_console(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange: secrets reach the document (description) and the console (warning path)
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
    description = f"uses {shaped} and {_SECRET_ENV}"
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\ndescription = "{description}"\n', encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / f"test_{shaped}.py").write_text("def test_x(:\n", encoding="utf-8")

    # Act
    code = main(["generate"])

    # Assert
    captured = capsys.readouterr()
    document = (repo / "docs/PROJECT_DOCS.md").read_text("utf-8")
    assert code == 0
    assert "warning: tests/test_" in captured.err
    for secret in (shaped, _SECRET_ENV):
        assert secret not in document
        assert secret not in captured.out + captured.err
    assert "[REDACTED]" in document
    assert "[REDACTED]" in captured.err


def test_verbose_output_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
    target = tmp_path / shaped
    target.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DOCSYNC_GITHUB_TOKEN", raising=False)

    # Act
    code = main(["generate", "--repo", str(target), "--out", str(target / "o.md"), "--verbose"])

    # Assert
    captured = capsys.readouterr()
    assert code == 0
    assert shaped not in captured.err
    assert "[REDACTED]" in captured.err


@pytest.mark.parametrize("out", ["a.md", "docs/x.md", "A.MD", "x.Md", "sub/../x.md"])
def test_out_ending_in_md_inside_repo_is_accepted(out: str) -> None:
    # Arrange / Act
    args = parse_args(["generate", "--out", out])

    # Assert
    assert args.out == Path(out)


@pytest.mark.parametrize(
    "out", ["a.txt", "a", "a.markdown", "docs/PROJECT_DOCS", ".md", "a.md.bak"]
)
def test_out_not_ending_in_md_is_rejected(out: str) -> None:
    # Arrange / Act / Assert
    with pytest.raises(UsageError, match=r"--out must end in \.md"):
        parse_args(["generate", "--out", out])


@pytest.mark.parametrize("out", ["../x.md", "sub/../../x.md", "../r2/x.md"])
def test_out_escaping_repo_via_dotdot_is_rejected(out: str) -> None:
    # Arrange / Act / Assert
    with pytest.raises(UsageError, match="--out must be inside --repo"):
        parse_args(["generate", "--out", out])


def test_out_absolute_path_outside_repo_is_rejected(tmp_path: Path) -> None:
    # Arrange
    outside = tmp_path.parent / "elsewhere.md"

    # Act / Assert
    with pytest.raises(UsageError, match="--out must be inside --repo"):
        parse_args(["generate", "--out", str(outside)])


def test_out_absolute_path_inside_repo_is_accepted(tmp_path: Path) -> None:
    # Arrange
    inside = tmp_path / "sub" / "o.md"

    # Act
    args = parse_args(["generate", "--out", str(inside)])

    # Assert
    assert args.out == inside


def test_out_in_sibling_directory_sharing_the_repo_name_prefix_is_rejected(
    tmp_path: Path,
) -> None:
    # Arrange
    repo = tmp_path / "r"
    sibling = tmp_path / "r2"
    repo.mkdir()
    sibling.mkdir()

    # Act / Assert
    with pytest.raises(UsageError, match="--out must be inside --repo"):
        parse_args(["generate", "--repo", str(repo), "--out", str(sibling / "x.md")])


def test_default_out_with_cwd_outside_repo_resolves_against_the_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    repo = tmp_path / "r"
    elsewhere = tmp_path / "elsewhere"
    repo.mkdir()
    elsewhere.mkdir()
    (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    monkeypatch.chdir(elsewhere)

    # Act
    args = parse_args(["generate", "--repo", str(repo)])
    code = main(["generate", "--repo", str(repo)])

    # Assert
    assert args.out == repo / "docs" / "PROJECT_DOCS.md"
    assert code == 0
    assert (repo / "docs" / "PROJECT_DOCS.md").is_file()
    assert not (elsewhere / "docs").exists()


def test_default_out_with_cwd_inside_repo_still_resolves_against_the_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    repo = tmp_path / "r"
    nested = repo / "sub" / "deeper"
    nested.mkdir(parents=True)
    (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    monkeypatch.chdir(nested)

    # Act
    code = main(["generate", "--repo", str(repo)])

    # Assert
    assert code == 0
    assert (repo / "docs" / "PROJECT_DOCS.md").is_file()
    assert not (nested / "docs").exists()


def test_default_out_with_default_repo_is_relative_docs_path() -> None:
    # Arrange / Act
    args = parse_args(["generate"])

    # Assert
    assert args.repo == Path(".")
    assert args.out == Path("docs/PROJECT_DOCS.md")


def test_explicit_relative_out_from_a_different_cwd_resolves_against_the_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: the cwd is a subdirectory of the repo; "../o.md" lands in the repo root
    repo = tmp_path / "r"
    nested = repo / "sub"
    nested.mkdir(parents=True)
    (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    monkeypatch.chdir(nested)

    # Act
    code = main(["generate", "--repo", str(repo), "--out", "../o.md"])

    # Assert
    assert code == 0
    assert (repo / "o.md").is_file()
    assert not (nested / "o.md").exists()


def test_explicit_relative_out_resolving_outside_the_repo_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: the cwd is outside the repo, so a bare relative name lands outside it
    repo = tmp_path / "r"
    elsewhere = tmp_path / "elsewhere"
    repo.mkdir()
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    # Act / Assert
    with pytest.raises(UsageError, match="--out must be inside --repo"):
        parse_args(["generate", "--repo", str(repo), "--out", "o.md"])


def test_check_default_out_from_outside_the_repo_compares_the_repo_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    repo = tmp_path / "r"
    elsewhere = tmp_path / "elsewhere"
    repo.mkdir()
    elsewhere.mkdir()
    (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    assert main(["generate", "--repo", str(repo)]) == 0

    # Act
    code = main(["check", "--repo", str(repo)])

    # Assert
    assert code == 0


def test_default_out_is_accepted_when_cwd_is_the_repo() -> None:
    # Arrange / Act
    args = parse_args(["check"])

    # Assert
    assert args.out == Path("docs/PROJECT_DOCS.md")


def test_out_rules_apply_to_check_too() -> None:
    # Arrange / Act / Assert
    with pytest.raises(UsageError, match=r"--out must end in \.md"):
        parse_args(["check", "--out", "x.txt"])


def test_invalid_out_exits_2_with_one_line_and_no_file_written(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange / Act
    code = main(["generate", "--out", "../escape.md"])

    # Assert
    assert code == 2
    assert "--out" in _assert_one_line_error(capsys)
    assert not (tmp_path.parent / "escape.md").exists()


def test_invalid_out_echoing_a_token_is_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act
    code = main(["generate", "--out", f"{_TOKEN_SHAPED}.txt"])

    # Assert
    err = _assert_one_line_error(capsys)
    assert code == 2
    assert _TOKEN_SHAPED not in err
    assert "[REDACTED]" in err


def _boom(error: BaseException) -> Any:
    def raiser(*args: object, **kwargs: object) -> None:
        raise error

    return raiser


def _run_module(*args: str, cwd: Path) -> Any:
    src = Path(__file__).resolve().parents[1] / "src"
    env = {**os.environ, "PYTHONPATH": str(src)}
    env.pop("DOCSYNC_GITHUB_TOKEN", None)
    return subprocess.run(
        [sys.executable, "-m", "docsync", *args],
        cwd=cwd, env=env, capture_output=True, text=True, check=False,
    )


def test_invalid_input_exit_2_no_traceback(tmp_path: Path) -> None:
    # Arrange / Act
    result = _run_module("generate", "--repo", "does-not-exist", cwd=tmp_path)

    # Assert
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert len(result.stderr.strip().splitlines()) == 1


def test_python_dash_m_docsync_help_runs(tmp_path: Path) -> None:
    # Arrange / Act
    result = _run_module("--help", cwd=tmp_path)

    # Assert
    assert result.returncode == 0
    assert "generate" in result.stdout
    assert "check" in result.stdout


def test_python_dash_m_docsync_generate_writes_file(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")

    # Act
    result = _run_module("generate", "--offline", cwd=tmp_path)

    # Assert
    assert result.returncode == 0
    assert result.stdout == "wrote docs/PROJECT_DOCS.md\n"
    assert (tmp_path / "docs" / "PROJECT_DOCS.md").is_file()


def test_keyboard_interrupt_exits_2_without_traceback(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(KeyboardInterrupt()))

    # Act
    code = main(["generate"])

    # Assert
    assert code == 2
    assert "interrupted" in _assert_one_line_error(capsys)


def test_broken_pipe_exits_2_without_traceback(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(BrokenPipeError()))

    # Act
    code = main(["generate"])

    # Assert
    assert code == 2
    assert "pipe" in _assert_one_line_error(capsys)


def test_write_failure_at_out_exits_2_without_traceback(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange: --out names an existing directory, so the write fails
    (repo / "out.md").mkdir()

    # Act
    code = main(["generate", "--out", "out.md"])

    # Assert
    assert code == 2
    assert "I/O error" in _assert_one_line_error(capsys)


def test_domain_error_exits_2_with_its_message(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(CollectError("cannot collect")))

    # Act
    code = main(["generate"])

    # Assert
    assert code == 2
    assert "docsync: error: cannot collect" in _assert_one_line_error(capsys)


def test_domain_error_message_is_redacted(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(CollectError(f"bad {_TOKEN_SHAPED}")))

    # Act
    code = main(["generate"])

    # Assert
    err = _assert_one_line_error(capsys)
    assert code == 2
    assert _TOKEN_SHAPED not in err


def test_domain_error_with_newlines_is_one_line(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(CollectError("a\nb\r\nc")))

    # Act
    code = main(["generate"])

    # Assert
    assert code == 2
    assert "a b c" in _assert_one_line_error(capsys)


def test_unexpected_exception_hides_type_and_text_without_verbose(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(RuntimeError("private detail")))

    # Act
    code = main(["generate"])

    # Assert
    err = _assert_one_line_error(capsys)
    assert code == 2
    assert "unexpected internal error" in err
    assert "RuntimeError" not in err
    assert "private detail" not in err


def test_unexpected_exception_shows_type_name_only_with_verbose(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setattr("docsync.cli.collect", _boom(RuntimeError("private detail")))

    # Act
    code = main(["generate", "--verbose"])

    # Assert
    err = capsys.readouterr().err
    assert code == 2
    assert "unexpected internal error (RuntimeError)" in err
    assert "private detail" not in err
    assert "Traceback" not in err


def test_help_is_not_turned_into_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange / Act / Assert
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == 0


def test_no_bare_except_in_source() -> None:
    # Arrange
    src = Path(__file__).resolve().parents[1] / "src" / "docsync"
    bare = [
        f"{path.name}:{node.lineno}"
        for path in src.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ExceptHandler) and node.type is None
    ]

    # Act / Assert
    assert bare == []


_DRIFT = 'drift detected: run "docsync generate" to update docs/PROJECT_DOCS.md\n'


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under root with its bytes and mtime, to prove nothing changed."""
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_check_in_sync_and_drift_exit_codes(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    main(["generate"])
    capsys.readouterr()

    # Act
    in_sync = main(["check"])
    in_sync_out = capsys.readouterr().out
    out_file = repo / "docs" / "PROJECT_DOCS.md"
    out_file.write_bytes(out_file.read_bytes() + b"edited by hand\n")
    drift = main(["check"])

    # Assert
    assert in_sync == 0
    assert in_sync_out == "in sync\n"
    assert drift == 1
    assert capsys.readouterr().out == _DRIFT


def test_ec_12_check_missing_file_is_drift(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange: no generate was run, so docs/PROJECT_DOCS.md does not exist

    # Act
    code = main(["check"])

    # Assert
    assert code == 1
    assert capsys.readouterr().out == _DRIFT


def test_check_missing_parent_directory_is_drift(repo: Path) -> None:
    # Arrange / Act
    code = main(["check", "--out", "no/such/dir/o.md"])

    # Assert
    assert code == 1


def test_check_read_error_exit_2(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange: --out is a directory, so reading it is an error, not drift
    (repo / "out.md").mkdir()

    # Act
    code = main(["check", "--out", "out.md"])

    # Assert
    assert code == 2
    assert "I/O error" in _assert_one_line_error(capsys)


def test_check_does_not_write_when_file_is_missing(repo: Path) -> None:
    # Arrange
    before = _snapshot(repo)

    # Act
    main(["check"])

    # Assert
    assert not (repo / "docs").exists()
    assert _snapshot(repo) == before


def test_check_does_not_write_when_file_has_drifted(repo: Path) -> None:
    # Arrange
    (repo / "docs").mkdir()
    (repo / "docs" / "PROJECT_DOCS.md").write_bytes(b"stale\n")
    before = _snapshot(repo)

    # Act
    code = main(["check"])

    # Assert
    assert code == 1
    assert _snapshot(repo) == before


def test_check_does_not_write_when_in_sync(repo: Path) -> None:
    # Arrange
    main(["generate"])
    before = _snapshot(repo)

    # Act
    code = main(["check"])

    # Assert
    assert code == 0
    assert _snapshot(repo) == before


def test_check_drift_prints_hint_and_no_diff(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    (repo / "docs").mkdir()
    (repo / "docs" / "PROJECT_DOCS.md").write_bytes(b"stale\n")

    # Act
    main(["check"])

    # Assert
    assert capsys.readouterr().out.splitlines() == [_DRIFT.strip()]


def test_check_crlf_copy_of_the_document_is_drift(repo: Path) -> None:
    # Arrange
    main(["generate"])
    out_file = repo / "docs" / "PROJECT_DOCS.md"
    out_file.write_bytes(out_file.read_bytes().replace(b"\n", b"\r\n"))

    # Act
    code = main(["check"])

    # Assert
    assert code == 1


def test_check_detects_a_change_in_the_repository(repo: Path) -> None:
    # Arrange
    main(["generate"])
    (repo / "pyproject.toml").write_text(_PYPROJECT.replace("demo", "renamed"), encoding="utf-8")

    # Act
    code = main(["check"])

    # Assert
    assert code == 1


def test_check_uses_the_same_hosted_configuration_as_generate(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    argv = ["--github-repo", "octo/demo"]
    main(["generate", *argv], _Session(_Response(200, _PAYLOAD)))

    # Act
    same = main(["check", *argv], _Session(_Response(200, _PAYLOAD)))
    changed = main(["check", *argv], _Session(_Response(200, {**_PAYLOAD, "topics": ["z"]})))

    # Assert
    assert same == 0
    assert changed == 1


def test_check_offline_flag_makes_no_requests(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    session = _Session()

    # Act
    main(["check", "--github-repo", "octo/demo", "--offline"], session)

    # Assert
    assert session.calls == []


def test_check_degraded_run_still_exits_0_and_warns_on_stderr(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", _SECRET_ENV)
    argv = ["--github-repo", "octo/demo"]
    main(["generate", *argv], _Session(_Response(404)))
    capsys.readouterr()

    # Act
    code = main(["check", *argv], _Session(_Response(404)))

    # Assert
    captured = capsys.readouterr()
    assert code == 0
    assert "warning: GitHub lookup failed" in captured.err
    assert captured.out == "in sync\n"


def test_check_output_is_redacted(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    out = f"{_TOKEN_SHAPED}.md"

    # Act
    code = main(["check", "--out", out])

    # Assert
    captured = capsys.readouterr()
    assert code == 1
    assert _TOKEN_SHAPED not in captured.out + captured.err
    assert "[REDACTED]" in captured.out


def test_no_not_implemented_error_remains_in_source() -> None:
    # Arrange
    src = Path(__file__).resolve().parents[1] / "src" / "docsync"

    # Act
    offenders = [
        path.name for path in src.rglob("*.py") if "NotImplementedError" in path.read_text("utf-8")
    ]

    # Assert
    assert offenders == []
