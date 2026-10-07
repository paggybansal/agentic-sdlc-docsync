"""Tests for docsync.cli (T13: parsing and validation, T14: generate)."""

from pathlib import Path
from typing import Any

import pytest

from docsync.cli import CliArgs, main, parse_args
from docsync.errors import UsageError

_TOKEN_SHAPED = "ghp_A1b2C3d4E5f6G7h8I9j0K1"


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
    cwd = tmp_path / "cwd"
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
    code = main(["generate", "--repo", str(target), "--out", "o.md", "--verbose"])

    # Assert
    captured = capsys.readouterr()
    assert code == 0
    assert shaped not in captured.err
    assert "[REDACTED]" in captured.err
