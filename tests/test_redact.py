"""Tests for docsync.redact (T3)."""

import pytest

from docsync.redact import PLACEHOLDER, redact

_BODY = "A1b2C3d4E5f6G7h8I9j0"


@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
def test_redact_token_prefix_is_replaced(prefix: str) -> None:
    # Arrange
    text = f"token {prefix}{_BODY} end"

    # Act
    result = redact(text)

    # Assert
    assert result == f"token {PLACEHOLDER} end"


def test_redact_literal_secret_is_replaced() -> None:
    # Arrange
    text = "the value is hunter2-value here"

    # Act
    result = redact(text, secrets=("hunter2-value",))

    # Assert
    assert result == f"the value is {PLACEHOLDER} here"


def test_redact_literal_secrets_longest_first() -> None:
    # Arrange
    text = "abc abcdef"

    # Act
    result = redact(text, secrets=("abc", "abcdef"))

    # Assert
    assert result == f"{PLACEHOLDER} {PLACEHOLDER}"


def test_redact_empty_secret_leaves_text_unchanged() -> None:
    # Arrange
    text = "nothing secret here"

    # Act
    result = redact(text, secrets=("",))

    # Assert
    assert result == text


def test_redact_whitespace_secret_leaves_text_unchanged() -> None:
    # Arrange
    text = "nothing secret here"

    # Act
    result = redact(text, secrets=("   ", "\n"))

    # Assert
    assert result == text


def test_redact_plain_text_is_unchanged() -> None:
    # Arrange
    text = "A plain description with ghp mentioned but no token."

    # Act
    result = redact(text)

    # Assert
    assert result == text


def test_redact_reads_no_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("DOCSYNC_GITHUB_TOKEN", "env-token-value")
    text = "contains env-token-value"

    # Act
    result = redact(text)

    # Assert
    assert result == text
