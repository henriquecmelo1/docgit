"""Branch operations."""

from pathlib import Path

from docgit.core.commits import CommitStore
from docgit.core.exceptions import BranchAlreadyExistsError
from docgit.core.hashing import resolve_commit_hash
from docgit.core.refs import Repository


class BranchService:
    """Create and list branch references."""

    def __init__(self, worktree: Path) -> None:
        self.repository = Repository(worktree)

    def list(self) -> list[tuple[str, bool]]:
        """Return branch names and whether each is active."""
        active = self.repository.read_head()
        return [(name, name == active) for name in self.repository.list_branches()]

    def create(self, name: str, commit_reference: str | None = None) -> str:
        """Create a branch without overwriting an existing reference."""
        self.repository.require_exists()
        if self.repository.branch_exists(name):
            raise BranchAlreadyExistsError(f"Branch já existe: {name}")
        source = commit_reference or self.repository.read_branch(
            self.repository.read_head()
        )
        if commit_reference:
            source = resolve_commit_hash(
                commit_reference,
                CommitStore(self.repository.root).all_hashes(),
            )
        else:
            CommitStore(self.repository.root).read(source)
        self.repository.write_branch(name, source)
        return source
