"""Domain exceptions raised by the core."""


class DocgitError(Exception):
    """Base class for expected docgit errors."""


class RepositoryAlreadyExistsError(DocgitError):
    """Raised when initializing an existing repository."""


class RepositoryNotFoundError(DocgitError):
    """Raised when a repository is required but missing."""


class RepositoryFormatError(DocgitError):
    """Raised when repository data is missing or malformed."""


class BranchNotFoundError(DocgitError):
    """Raised when a branch does not exist."""


class BranchAlreadyExistsError(DocgitError):
    """Raised when creating an existing branch."""


class InvalidBranchNameError(DocgitError):
    """Raised when a branch name is unsafe or invalid."""


class CommitNotFoundError(DocgitError):
    """Raised when a commit cannot be found."""


class AmbiguousCommitError(DocgitError):
    """Raised when a commit prefix identifies multiple commits."""


class UncommittedChangesError(DocgitError):
    """Raised when checkout would discard workspace changes."""


class ProviderError(DocgitError):
    """Raised when the document provider cannot complete an operation."""


class AuthorNotConfiguredError(DocgitError):
    """Raised when Git author configuration is unavailable."""


class ProviderNotConfiguredError(DocgitError):
    """Raised when the CLI has no document provider factory."""
