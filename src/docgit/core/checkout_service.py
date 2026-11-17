"""Branch checkout use case."""

from pathlib import Path

from docgit.core.blobs import BlobStore
from docgit.core.commits import CommitStore
from docgit.core.exceptions import UncommittedChangesError
from docgit.core.hashing import sha256_bytes
from docgit.core.models import Commit, RepoConfig
from docgit.core.ports import DocumentProvider, IdentityNormalizer, Normalizer
from docgit.core.refs import Repository


class CheckoutService:
    """Switch branches while protecting uncommitted workspace changes."""

    def __init__(
        self,
        worktree: Path,
        provider: DocumentProvider,
        normalizer: Normalizer | None = None,
    ) -> None:
        self.repository = Repository(worktree)
        self.provider = provider
        self.normalizer = normalizer or IdentityNormalizer()

    def checkout(self, branch: str, force: bool = False) -> str:
        """Replace the workspace with a branch snapshot and update HEAD."""
        self.repository.require_exists()
        target_hash = self.repository.read_branch(branch)
        config = self.repository.read_config()
        current_hash = self.repository.read_branch(self.repository.read_head())
        commits = CommitStore(self.repository.root)
        current = commits.read(current_hash)
        dirty = self._has_uncommitted_changes(config, current)
        if dirty and not force:
            raise UncommittedChangesError(
                "Há alterações não commitadas. Faça commit ou use --force."
            )
        target = commits.read(target_hash)
        content = BlobStore(self.repository.root).read(target.blob)
        self.provider.replace_content(content)
        self.repository.write_head(branch)
        self.repository.write_config(
            RepoConfig(
                document_id=config.document_id,
                repository_name=config.repository_name,
                format_version=config.format_version,
                modified_time=self.provider.modified_time(),
            )
        )
        return target.hash

    def _has_uncommitted_changes(self, config: RepoConfig, current: Commit) -> bool:
        """Compare provider state with the active commit."""
        if self.provider.modified_time() == config.modified_time:
            return False
        content = self.normalizer.normalize(self.provider.export_docx())
        return sha256_bytes(content) != current.blob
