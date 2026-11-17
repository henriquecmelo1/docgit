"""Small interfaces consumed by the core."""

from datetime import datetime
from typing import Protocol


class DocumentProvider(Protocol):
    """Provider for the document used as the workspace."""

    def export_docx(self) -> bytes:
        """Export the current document."""

    def replace_content(self, docx: bytes) -> None:
        """Replace the document content."""

    def modified_time(self) -> str:
        """Return the provider's current modification timestamp."""


class Clock(Protocol):
    """Clock abstraction for deterministic tests."""

    def now(self) -> datetime:
        """Return the current UTC datetime."""


class Normalizer(Protocol):
    """Normalizer for exported document bytes."""

    def normalize(self, docx: bytes) -> bytes:
        """Return deterministic document bytes."""


class IdentityNormalizer:
    """Normalizer used until the Google export spike defines ZIP rules."""

    def normalize(self, docx: bytes) -> bytes:
        """Return bytes unchanged."""
        return docx
