"""Tests for docsync.redact (T3)."""

import pytest

from docsync.redact import PLACEHOLDER, redact

_BODY = "A1b2C3d4E5f6G7h8I9j0"


@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
def test_ec_9_redact_token_prefix_is_replaced(prefix: str) -> None:
    # Arrange
    text = f"token {prefix}{_BODY} end"

    # Act
    result = redact(text)

    # Assert
    assert result == f"token {PLACEHOLDER} end"


def test_ec_9_redact_literal_secret_is_replaced() -> None:
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


def test_redact_authorization_header_value_is_replaced() -> None:
    # Arrange
    text = "Authorization: Basic dXNlcjpwYXNz next"

    # Act
    result = redact(text)

    # Assert
    assert result == f"Authorization: {PLACEHOLDER} next"


def test_redact_bearer_value_is_replaced() -> None:
    # Arrange
    text = "sent Bearer abc.DEF-123 to host"

    # Act
    result = redact(text)

    # Assert
    assert result == f"sent Bearer {PLACEHOLDER} to host"


def test_redact_url_userinfo_is_replaced() -> None:
    # Arrange
    text = "dep git+https://user:s3cr3t@example.com/repo.git"

    # Act
    result = redact(text)

    # Assert
    assert result == f"dep git+https://{PLACEHOLDER}@example.com/repo.git"


def test_redact_url_without_userinfo_is_unchanged() -> None:
    # Arrange
    text = "see https://example.com/a:b/c"

    # Act
    result = redact(text)

    # Assert
    assert result == text


@pytest.mark.parametrize("word", ["token", "secret", "password", "passwd", "key", "credential"])
def test_redact_key_equals_value_is_replaced(word: str) -> None:
    # Arrange
    text = f"{word}=abc123 after"

    # Act
    result = redact(text)

    # Assert
    assert result == f"{word}={PLACEHOLDER} after"


@pytest.mark.parametrize("word", ["token", "secret", "password", "passwd", "key", "credential"])
def test_redact_key_colon_value_is_replaced(word: str) -> None:
    # Arrange
    text = f"{word}: abc123 after"

    # Act
    result = redact(text)

    # Assert
    assert result == f"{word}: {PLACEHOLDER} after"


def test_redact_compound_key_name_is_replaced() -> None:
    # Arrange
    text = "api_key = 'abc 123'"

    # Act
    result = redact(text)

    # Assert
    assert result == f"api_key = {PLACEHOLDER}"


def test_redact_key_value_with_other_key_is_unchanged() -> None:
    # Arrange
    text = "name=docsync version: 0.1.0"

    # Act
    result = redact(text)

    # Assert
    assert result == text


def test_redact_literal_secret_applied_before_patterns() -> None:
    # Arrange
    text = "label: plain-secret-value"

    # Act
    result = redact(text, secrets=("plain-secret-value",))

    # Assert
    assert result == f"label: {PLACEHOLDER}"


def test_redact_is_idempotent() -> None:
    # Arrange
    text = (
        f"Authorization: Bearer abc ghp_{_BODY} https://u:p@h.io "
        "password=x token: y api_key='a b' Bearer zzz"
    )
    once = redact(text, secrets=("zzz",))

    # Act
    twice = redact(once, secrets=("zzz",))

    # Assert
    assert twice == once


def test_redact_same_input_gives_same_output() -> None:
    # Arrange
    text = f"password=x ghp_{_BODY}"

    # Act / Assert
    assert redact(text) == redact(text)
