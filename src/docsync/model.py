"""Data model: the sentinel and the immutable facts record (FR-3, FR-13)."""

from dataclasses import dataclass

NOT_FOUND = "Not Found"
SCHEMA_VERSION = "1"

FieldValue = str | tuple[str, ...]


@dataclass(frozen=True)
class ProjectFacts:
    """Everything the renderer needs; holds no timestamp or hash (FR-5)."""

    overview: dict[str, FieldValue]
    identity: dict[str, FieldValue]
    hosted: dict[str, FieldValue]
    modules: tuple[str, ...]
    entry_points: tuple[str, ...]
    dependencies: tuple[str, ...]
    optional_dependencies: dict[str, tuple[str, ...]]
    tests: dict[str, FieldValue]
    warnings: tuple[str, ...]
