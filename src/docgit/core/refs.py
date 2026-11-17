"""Repository layout, configuration, HEAD and branch references."""

import json
import re
from pathlib import Path

from docgit.core.atomic import atomic_write_text
from docgit.core.exceptions import (
    BranchNotFoundError,
    InvalidBranchNameError,
    RepositoryFormatError,
    RepositoryNotFoundError,
)
from docgit.core.models import RepoConfig

_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class Repository:
    """Access the files and references in a ``.docgit`` directory."""

    def __init__(self, worktree: Path) -> None:
        self.worktree = worktree
        self.root = worktree / ".docgit"
        self.refs_root = self.root / "refs" / "heads"
        self.commits_root = self.root / "commits"
        self.blobs_root = self.root / "blobs"

    def create_layout(self) -> None:
        """Create the repository directories."""
        for path in (self.refs_root, self.commits_root, self.blobs_root):
            path.mkdir(parents=True, exist_ok=True)

    def require_exists(self) -> None:
        """Require an initialized repository."""
        if not self.root.is_dir():
            raise RepositoryNotFoundError("Nenhum repositório docgit encontrado.")

    def config_path(self) -> Path:
        """Return the configuration path."""
        return self.root / "config.json"

    def read_config(self) -> RepoConfig:
        """Read repository configuration."""
        self.require_exists()
        try:
            with self.config_path().open(encoding="utf-8") as stream:
                return RepoConfig.from_dict(json.load(stream))
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise RepositoryFormatError("config.json inválido.") from error

    def write_config(self, config: RepoConfig) -> None:
        """Write repository configuration atomically."""
        atomic_write_text(
            self.config_path(),
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )

    def read_head(self) -> str:
        """Read the active branch name."""
        self.require_exists()
        try:
            return (self.root / "HEAD").read_text(encoding="utf-8").strip()
        except OSError as error:
            raise RepositoryFormatError("HEAD inválido.") from error

    def write_head(self, branch: str) -> None:
        """Update HEAD atomically."""
        atomic_write_text(self.root / "HEAD", f"{branch}\n")

    def branch_path(self, branch: str) -> Path:
        """Return a validated branch reference path."""
        if (
            not _BRANCH_PATTERN.fullmatch(branch)
            or branch.startswith(("/", "."))
            or any(part in {"", ".", ".."} for part in branch.split("/"))
        ):
            raise InvalidBranchNameError(f"Nome de branch inválido: {branch}")
        path = self.refs_root / branch
        try:
            path.relative_to(self.refs_root)
        except ValueError as error:
            raise InvalidBranchNameError(
                f"Nome de branch inválido: {branch}"
            ) from error
        return path

    def list_branches(self) -> list[str]:
        """List branch names in stable order."""
        self.require_exists()
        return sorted(
            path.relative_to(self.refs_root).as_posix()
            for path in self.refs_root.rglob("*")
            if path.is_file()
        )

    def read_branch(self, branch: str) -> str:
        """Read a branch commit hash."""
        path = self.branch_path(branch)
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise BranchNotFoundError(f"Branch não encontrada: {branch}") from error
        if not value:
            raise RepositoryFormatError(f"Branch vazia: {branch}")
        return value

    def write_branch(self, branch: str, commit_hash: str) -> None:
        """Write a branch reference atomically."""
        atomic_write_text(self.branch_path(branch), f"{commit_hash}\n")

    def branch_exists(self, branch: str) -> bool:
        """Return whether a branch reference exists."""
        return self.branch_path(branch).is_file()
