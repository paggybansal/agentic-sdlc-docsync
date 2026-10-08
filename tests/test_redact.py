"""Tests for docsync.redact (T3, T4, T20)."""

import ast
import hashlib
import re
import time
from pathlib import Path
from re import _constants, _parser

import pytest

from docsync import redact as redact_module
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


@pytest.mark.parametrize("word", ["token", "secret", "password", "passwd", "credential"])
def test_redact_key_equals_value_is_replaced(word: str) -> None:
    # Arrange
    text = f"{word}=abc123 after"

    # Act
    result = redact(text)

    # Assert
    assert result == f"{word}={PLACEHOLDER} after"


@pytest.mark.parametrize("word", ["token", "secret", "password", "passwd", "credential"])
def test_redact_key_colon_value_is_replaced(word: str) -> None:
    # Arrange
    text = f"{word}: abc123 after"

    # Act
    result = redact(text)

    # Assert
    assert result == f"{word}: {PLACEHOLDER} after"


def test_redact_compound_key_name_is_replaced() -> None:
    # Arrange
    text = "api_key = 'A1b2C3d4E5f6G7h8I9j0K1'"

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
        "password=x token: y api_key='A1b2C3d4E5f6G7h8I9j0K1' Bearer zzzzzzzz"
    )
    once = redact(text, secrets=("zzzzzzzz",))

    # Act
    twice = redact(once, secrets=("zzzzzzzz",))

    # Assert
    assert twice == once


def test_redact_same_input_gives_same_output() -> None:
    # Arrange
    text = f"password=x ghp_{_BODY}"

    # Act / Assert
    assert redact(text) == redact(text)


# --- T20: hardened redactor (CR-1, CR-2, CR-3) -------------------------------------------------

_GH_TOKEN = "ghp_A1b2C3d4E5f6G7h8I9j0K1L2M3N4O5P6Q7R8"
_MIXED_BLOB = "Zm9vYmFyQmF6UXV4MTIzNDU2Nzg5MEFCQ0RFRkdISUpLTE1O"
_JWT = (
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk"
)


def test_mixed_blob_fixture_is_long_enough_and_really_mixed() -> None:
    # Arrange / Act / Assert
    assert len(_MIXED_BLOB) >= 40
    assert any(c.isupper() for c in _MIXED_BLOB)
    assert any(c.islower() for c in _MIXED_BLOB)
    assert any(c.isdigit() for c in _MIXED_BLOB)


@pytest.mark.parametrize(
    "secret",
    [
        "sk-ant-api03-abcdefghijklmnop1234",
        "sk-proj1234567890abcdefgh",
        _GH_TOKEN,
        "github_pat_11ABCDEFG0abcdefghijkl_mnopqrstuvwxyz0123456789",
        "gho_A1b2C3d4E5f6G7h8I9j0K1L2",
        "AKIAIOSFODNN7EXAMPLE",
        "xoxb-1234567890-abcdefghij",
        "xoxp-1234567890-1234567890-abcdefghijkl",
        _JWT,
    ],
    ids=lambda s: s[:12],
)
def test_ec_9_each_provider_token_class_is_replaced(secret: str) -> None:
    # Arrange
    text = f"before {secret} after"

    # Act
    result = redact(text)

    # Assert
    assert result == f"before {PLACEHOLDER} after"


@pytest.mark.parametrize(
    "header",
    [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    ],
)
def test_ec_9_pem_private_key_header_and_body_are_replaced(header: str) -> None:
    # Arrange
    body = "MIIEowIBAAKCAQEAabc+/def==\nQWxhZGRpbjpvcGVuIHNlc2FtZQ=="
    text = f"{header}\n{body}\n-----END PRIVATE KEY-----"

    # Act
    result = redact(text)

    # Assert
    assert "MIIEowIBAAKCAQEA" not in result
    assert "QWxhZGRpbjpvcGVuIHNlc2FtZQ" not in result
    assert "BEGIN" not in result
    assert result.startswith(PLACEHOLDER)


def test_ec_9_token_only_userinfo_of_20_or_more_characters_is_replaced() -> None:
    # Arrange
    text = "see git+https://abcdefghij0123456789klmnop@example.com/org/repo.git"

    # Act
    result = redact(text)

    # Assert
    assert result == f"see git+https://{PLACEHOLDER}@example.com/org/repo.git"


def test_ec_9_mixed_case_base64_blob_is_replaced() -> None:
    # Arrange
    text = f"blob {_MIXED_BLOB} end"

    # Act
    result = redact(text)

    # Assert
    assert result == f"blob {PLACEHOLDER} end"


def test_ec_9_mixed_case_base64_blob_with_padding_is_replaced_including_the_padding() -> None:
    # Arrange
    text = f"x {_MIXED_BLOB}== y"

    # Act
    result = redact(text)

    # Assert
    assert result == f"x {PLACEHOLDER} y"


def test_blob_longer_than_one_chunk_is_redacted_in_chunks() -> None:
    # Arrange: 9000 mixed characters span three 4096-character chunks (the last one is 808)
    text = "aA1" * 3000

    # Act
    result = redact(text)

    # Assert
    assert result == PLACEHOLDER * 3


@pytest.mark.parametrize(
    "benign",
    [
        hashlib.sha256(b"docsync").hexdigest(),
        hashlib.sha1(b"docsync").hexdigest(),
        "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "0123456789012345678901234567890123456789",
    ],
    ids=["sha256-hex", "sha1-hex", "lowercase-only", "uppercase-only", "mixed-no-digit", "digits"],
)
def test_blob_rule_does_not_mangle_hashes_or_single_case_strings(benign: str) -> None:
    # Arrange
    text = f"hash: {benign}"

    # Act
    result = redact(text)

    # Assert
    assert result == text


def test_sha256_hex_is_exactly_64_characters_in_the_false_positive_fixture() -> None:
    # Arrange / Act / Assert
    assert len(hashlib.sha256(b"docsync").hexdigest()) == 64


_BENIGN_LINES = [
    "| Dependency | " + ", ".join(f"runtimedep{i:02d}>=1.{i}" for i in range(30)) + " |",
    "src/docsync/collectors/some_really_long_package_name/another_nested_package/module_name.py",
    "The quick brown fox jumps over the lazy dog; the key is under the doormat.",
    "keygen = 1",
    "keyring=abc",
    "API key: rotate it",
    "key = value",
    "monkey: banana",
    "tokenizer = fast",
    "secretary: Jane",
    "Keywords: python, docs",
    "risk-assessment-framework-with-a-rather-long-name",
    "ssh://git@github.com/org/repo.git",
    "bearer of bad news",
    "released 2026-10-08T12:34:56Z by the build",
    "| Authors | Zed, Amy |",
]


@pytest.mark.parametrize("line", _BENIGN_LINES, ids=lambda s: s[:24])
def test_ordinary_content_is_not_mangled(line: str) -> None:
    # Arrange / Act
    result = redact(line)

    # Assert
    assert result == line


def test_cr_3_api_key_assignment_with_a_github_token_is_replaced() -> None:
    # Arrange
    text = f"api_key={_GH_TOKEN}"

    # Act
    result = redact(text)

    # Assert
    assert result == f"api_key={PLACEHOLDER}"


@pytest.mark.parametrize(
    "assignment",
    [
        "deploy_token=Xk9fA2bQ7mZ3pL5vT8wRq1",
        "client_secret: Xk9fA2bQ7mZ3pL5vT8wRq1sD4",
        "auth_key = 'Zm9vYmFyQmF6UXV4MTIzNDU2'",
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    ],
    ids=lambda s: s[:14],
)
def test_cr_3_token_shaped_assignment_of_20_or_more_characters_is_replaced(
    assignment: str,
) -> None:
    # Arrange / Act
    result = redact(assignment)

    # Assert
    assert result.endswith(PLACEHOLDER)
    assert assignment.split("=", 1)[-1].strip(" '") not in result


@pytest.mark.parametrize(
    "assignment", ["key=short", "key: 19charsabcdefghijkl", "api_key = 'abc 123'"]
)
def test_cr_3_weak_key_assignment_below_20_characters_is_left_alone(assignment: str) -> None:
    # Arrange / Act
    result = redact(assignment)

    # Assert
    assert result == assignment


def test_unterminated_quoted_secret_value_is_replaced() -> None:
    # Arrange
    text = 'password = "unterminated secret value'

    # Act
    result = redact(text)

    # Assert
    assert result == f"password = {PLACEHOLDER}"


def test_authorization_header_with_a_scheme_is_replaced_with_its_value() -> None:
    # Arrange
    text = "Authorization: Bearer abc123def456"

    # Act
    result = redact(text)

    # Assert
    assert result == f"Authorization: {PLACEHOLDER}"


def test_bearer_value_shorter_than_8_characters_is_left_alone() -> None:
    # Arrange / Act / Assert
    assert redact("Bearer abc") == "Bearer abc"


_EVERY_CLASS = " | ".join(
    [
        _GH_TOKEN,
        "sk-ant-api03-abcdefghijklmnop1234",
        "AKIAIOSFODNN7EXAMPLE",
        "xoxb-1234567890-abcdefghij",
        _JWT,
        "-----BEGIN PRIVATE KEY-----\nMIIEowIBAAKCAQEAabc+/def==\n-----END PRIVATE KEY-----",
        "Authorization: Bearer abc123def456",
        "Bearer abcdefgh12345678",
        "git+https://deploy:s3cr3t@example.com/x.git",
        "git+https://abcdefghij0123456789klmnop@example.com/x.git",
        "password=hunter2 token: y client_secret: Xk9fA2bQ7mZ3pL5vT8wRq1sD4",
        'auth_key = "Zm9vYmFyQmF6UXV4MTIzNDU2"',
        f"blob {_MIXED_BLOB}==",
        "password = \"unterminated",
    ]
)


def test_redact_is_a_no_op_on_already_redacted_text_for_every_pattern_class() -> None:
    # Arrange
    once = redact(_EVERY_CLASS, secrets=("hunter2",))

    # Act
    twice = redact(once, secrets=("hunter2",))

    # Assert
    assert once != _EVERY_CLASS
    assert twice == once


def test_every_pattern_class_is_gone_from_the_combined_sample() -> None:
    # Arrange / Act
    result = redact(_EVERY_CLASS, secrets=("hunter2",))

    # Assert
    for leaked in (
        "ghp_", "sk-ant", "AKIA", "xoxb-", "eyJ", "MIIEow", "abc123def456", "s3cr3t",
        "abcdefghij0123456789klmnop", "hunter2", "Xk9fA2bQ7mZ3pL5vT8wRq1sD4",
        "Zm9vYmFyQmF6UXV4MTIzNDU2", _MIXED_BLOB, "unterminated",
    ):
        assert leaked not in result


_PATHOLOGICAL = {
    "one long word": "a" * 20000,
    "dash word then equals": "a-" * 10000 + "=",
    "repeated scheme": "a://" * 5000,
    "long userinfo without an at sign": "http://" + "a:" * 10000,
    "repeated token keyword": "token=" * 3300,
    "keyword then whitespace": "password:" + " " * 20000 + "x",
    "repeated authorization header": "Authorization: Bearer " * 900,
    "repeated jwt prefix": "eyJ" * 6600,
    "repeated github prefix": "ghp_" * 5000,
    "repeated sk prefix": "sk-" * 6600,
    "repeated pem header": "-----BEGIN PRIVATE KEY-----" * 740,
    "long mixed-case run": "aA1" * 6700,
    "long hex run": "0123456789abcdef" * 1250,
    "bearer then whitespace": "bearer" + " " * 20000,
    "whitespace only": " " * 20000,
    "unterminated quote": 'password="' + "a" * 20000,
    "dots and slashes": "a.b/" * 5000,
    "equals run": "key" + "=" * 20000,
}


@pytest.mark.perf
@pytest.mark.parametrize("text", list(_PATHOLOGICAL.values()), ids=list(_PATHOLOGICAL))
def test_redos_regression_pathological_input_completes_under_1_second(text: str) -> None:
    # Arrange
    started = time.perf_counter()

    # Act
    redact(text)
    elapsed = time.perf_counter() - started

    # Assert
    assert elapsed < 1.0


def test_pathological_inputs_are_really_about_20000_characters() -> None:
    # Arrange / Act
    sizes = [len(text) for text in _PATHOLOGICAL.values()]

    # Assert
    assert min(sizes) >= 18000


_REPEAT_OPS = {_constants.MAX_REPEAT, _constants.MIN_REPEAT, _constants.POSSESSIVE_REPEAT}


def _unbounded_repeats(pattern: re.Pattern[str]) -> list[object]:
    """Every repeat in ``pattern`` whose upper bound is open-ended."""
    found: list[object] = []

    def walk(node: object) -> None:
        if isinstance(node, _parser.SubPattern):
            for op, argument in node.data:
                if op in _REPEAT_OPS and argument[1] == _constants.MAXREPEAT:
                    found.append(op)
                walk(argument)
        elif isinstance(node, tuple | list):
            for item in node:
                walk(item)

    walk(_parser.parse(pattern.pattern, pattern.flags))
    return found


def test_the_bound_checker_detects_unbounded_quantifiers() -> None:
    # Arrange / Act / Assert
    assert _unbounded_repeats(re.compile("a+")) != []
    assert _unbounded_repeats(re.compile("a*b")) != []
    assert _unbounded_repeats(re.compile("a{2,}")) != []
    assert _unbounded_repeats(re.compile("(?:ab+)?c")) != []


def test_the_bound_checker_accepts_bounded_quantifiers() -> None:
    # Arrange / Act / Assert
    assert _unbounded_repeats(re.compile(r"a{1,5}b?(?:c{0,3}|d{2})")) == []


def test_every_quantifier_in_every_redaction_pattern_is_bounded() -> None:
    # Arrange / Act
    offenders = [
        pattern.pattern
        for pattern, _ in redact_module._RULES
        if _unbounded_repeats(pattern)
    ]

    # Assert
    assert offenders == []


def test_patterns_are_compiled_once_into_a_module_level_tuple() -> None:
    # Arrange / Act / Assert
    assert isinstance(redact_module._RULES, tuple)
    assert all(isinstance(p, re.Pattern) for p, _ in redact_module._RULES)


def test_redact_does_not_compile_patterns_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("re.compile called while redacting")

    monkeypatch.setattr(re, "compile", forbidden)

    # Act
    result = redact(f"token {_GH_TOKEN} and password=x")

    # Assert
    assert _GH_TOKEN not in result


def test_only_the_cli_module_imports_the_redactor() -> None:
    # Arrange
    src = Path(__file__).resolve().parents[1] / "src" / "docsync"
    importers = set()
    for path in src.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            from_redact = isinstance(node, ast.ImportFrom) and (
                node.module == "docsync.redact"
                or (node.module == "docsync" and any(a.name == "redact" for a in node.names))
            )
            plain = isinstance(node, ast.Import) and any(
                a.name == "docsync.redact" for a in node.names
            )
            if from_redact or plain:
                importers.add(path.name)

    # Act / Assert
    assert importers == {"cli.py"}
