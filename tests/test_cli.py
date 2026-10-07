"""Tests for docsync.cli (T13: parsing and validation)."""

from pathlib import Path

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
