"""Content-addressed blob storage."""

from pathlib import Path

from docgit.core.atomic import atomic_write_bytes
from docgit.core.exceptions import RepositoryFormatError
from docgit.core.hashing import sha256_bytes


class BlobStore:
    """Store normalized document snapshots by SHA-256."""

    def __init__(self, repository_root: Path) -> None:
        self.root = repository_root / "blobs"

    def save(self, data: bytes) -> str:
        """Store data if absent and return its hash."""
        digest = sha256_bytes(data)
        path = self.root / f"{digest}.docx"
        if not path.exists():
            atomic_write_bytes(path, data)
        return digest

    def read(self, digest: str) -> bytes:
        """Read a blob by hash."""
        path = self.root / f"{digest}.docx"
        try:
            return path.read_bytes()
        except OSError as error:
            raise RepositoryFormatError(f"Blob não encontrado: {digest}") from error
