"""Tests for docsync.errors and docsync.model (T1)."""

import dataclasses

import pytest
import requests

from docsync import model
from docsync.errors import CollectError, DocsyncError, GitHubError, UsageError
from docsync.model import NOT_FOUND, SCHEMA_VERSION, ProjectFacts


def _facts() -> ProjectFacts:
    return ProjectFacts(
        overview={"name": NOT_FOUND, "description": NOT_FOUND},
        identity={},
        hosted={},
        modules=(),
        entry_points=(),
        dependencies=(),
        optional_dependencies={},
        tests={},
        warnings=(),
    )


def test_not_found_sentinel_has_exact_spelling() -> None:
    # Arrange / Act / Assert
    assert NOT_FOUND == "Not Found"


def test_schema_version_is_one() -> None:
    # Arrange / Act / Assert
    assert SCHEMA_VERSION == "1"


@pytest.mark.parametrize("error", [UsageError, CollectError, GitHubError])
def test_domain_errors_derive_from_docsync_error(error: type[Exception]) -> None:
    # Arrange / Act / Assert
    assert issubclass(error, DocsyncError)


def test_docsync_error_is_an_exception() -> None:
    # Arrange / Act / Assert
    assert issubclass(DocsyncError, Exception)


def test_project_facts_is_frozen() -> None:
    # Arrange
    facts = _facts()

    # Act / Assert
    with pytest.raises(dataclasses.FrozenInstanceError):
        facts.modules = ("x.py",)  # type: ignore[misc]


def test_project_facts_has_no_timestamp_or_hash_field() -> None:
    # Arrange
    names = {f.name for f in dataclasses.fields(ProjectFacts)}

    # Act
    volatile = {n for n in names if any(k in n for k in ("time", "date", "hash", "stamp"))}

    # Assert
    assert volatile == set()


def test_model_has_no_field_wrapper_class() -> None:
    # Arrange / Act / Assert
    assert not hasattr(model, "Field")


def test_autouse_fixture_blocks_real_requests() -> None:
    # Arrange
    session = requests.Session()

    # Act / Assert
    with pytest.raises(AssertionError, match="real network access"):
        session.get("https://api.github.com/repos/o/n")
