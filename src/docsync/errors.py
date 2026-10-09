"""Domain exceptions for docsync (FR-19)."""


class DocsyncError(Exception):
    """Base class for every domain error raised by docsync."""


class UsageError(DocsyncError):
    """Invalid input or command-line usage; maps to exit code 2."""


class CollectError(DocsyncError):
    """A local repository fact could not be collected."""


class GitHubError(DocsyncError):
    """The hosted-metadata lookup failed."""
