"""Immutable values used by the version-control core."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Commit:
    """Metadata for an immutable commit."""

    hash: str
    parent: str | None
    blob: str
    message: str
    author: str
    timestamp: str

    def without_hash(self) -> dict[str, Any]:
        """Return the fields used to calculate the commit hash."""
        return {
            "parent": self.parent,
            "blob": self.blob,
            "message": self.message,
            "author": self.author,
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the commit to its on-disk representation."""
        return {"hash": self.hash, **self.without_hash()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Commit":
        """Create a commit from validated JSON data."""
        return cls(
            hash=str(data["hash"]),
            parent=data["parent"],
            blob=str(data["blob"]),
            message=str(data["message"]),
            author=str(data["author"]),
            timestamp=str(data["timestamp"]),
        )


@dataclass(frozen=True)
class RepoConfig:
    """Repository configuration stored in ``config.json``."""

    document_id: str
    repository_name: str
    format_version: int
    modified_time: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the configuration."""
        return {
            "documentId": self.document_id,
            "repository": self.repository_name,
            "formatVersion": self.format_version,
            "modifiedTime": self.modified_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RepoConfig":
        """Create configuration from JSON data."""
        return cls(
            document_id=str(data["documentId"]),
            repository_name=str(data["repository"]),
            format_version=int(data["formatVersion"]),
            modified_time=str(data["modifiedTime"]),
        )


@dataclass(frozen=True)
class OperationResult:
    """Result returned by mutating core services."""

    changed: bool
    commit_hash: str | None = None
    message: str = ""
