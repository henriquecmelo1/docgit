"""Immutable commit metadata storage."""

import json
from pathlib import Path

from docgit.core.atomic import atomic_write_text
from docgit.core.exceptions import CommitNotFoundError, RepositoryFormatError
from docgit.core.hashing import commit_hash
from docgit.core.models import Commit


class CommitStore:
    """Store and load immutable commit metadata."""

    def __init__(self, repository_root: Path) -> None:
        self.root = repository_root / "commits"

    def save(self, commit: Commit) -> None:
        """Write a commit once and reject conflicting rewrites."""
        path = self.root / f"{commit.hash}.json"
        if path.exists():
            try:
                existing = self.read(commit.hash)
            except RepositoryFormatError:
                raise
            if existing != commit:
                raise RepositoryFormatError(f"Commit imutável já existe: {commit.hash}")
            return
        atomic_write_text(
            path,
            json.dumps(commit.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )

    def read(self, digest: str) -> Commit:
        """Read a commit by its complete hash."""
        path = self.root / f"{digest}.json"
        try:
            with path.open(encoding="utf-8") as stream:
                data = json.load(stream)
            commit = Commit.from_dict(data)
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise RepositoryFormatError(f"Commit inválido: {digest}") from error
        if commit.hash != digest:
            raise RepositoryFormatError(f"Hash de commit inconsistente: {digest}")
        if commit_hash(commit) != digest:
            raise RepositoryFormatError(f"Conteúdo de commit inconsistente: {digest}")
        return commit

    def all_hashes(self) -> list[str]:
        """List complete commit hashes."""
        return sorted(path.stem for path in self.root.glob("*.json"))

    def resolve(self, digest: str) -> Commit:
        """Resolve a complete hash or prefix and load its commit."""
        from docgit.core.hashing import resolve_commit_hash

        try:
            return self.read(resolve_commit_hash(digest, self.all_hashes()))
        except CommitNotFoundError:
            raise
