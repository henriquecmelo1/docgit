"""Commit history queries."""

from pathlib import Path

from docgit.core.commits import CommitStore
from docgit.core.models import Commit
from docgit.core.refs import Repository


class LogService:
    """Read the active branch history."""

    def __init__(self, worktree: Path) -> None:
        self.repository = Repository(worktree)

    def history(self) -> list[Commit]:
        """Return commits from newest to oldest."""
        self.repository.require_exists()
        commits = CommitStore(self.repository.root)
        current = self.repository.read_branch(self.repository.read_head())
        history: list[Commit] = []
        while current:
            commit = commits.read(current)
            history.append(commit)
            current = commit.parent or ""
        return history
