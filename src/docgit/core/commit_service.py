"""Commit creation use case."""

from pathlib import Path

from docgit.core.blobs import BlobStore
from docgit.core.clock import SystemClock
from docgit.core.commits import CommitStore
from docgit.core.hashing import commit_hash, utc_timestamp
from docgit.core.models import Commit, OperationResult, RepoConfig
from docgit.core.ports import Clock, DocumentProvider, IdentityNormalizer, Normalizer
from docgit.core.refs import Repository


class CommitService:
    """Create immutable commits for the active branch."""

    def __init__(
        self,
        worktree: Path,
        provider: DocumentProvider,
        author: str,
        clock: Clock | None = None,
        normalizer: Normalizer | None = None,
    ) -> None:
        self.repository = Repository(worktree)
        self.provider = provider
        self.author = author
        self.clock = clock or SystemClock()
        self.normalizer = normalizer or IdentityNormalizer()

    def create(self, message: str) -> OperationResult:
        """Export the workspace and create a commit when content changed."""
        self.repository.require_exists()
        if not message.strip():
            raise ValueError("A mensagem do commit não pode ser vazia.")
        head = self.repository.read_head()
        parent_hash = self.repository.read_branch(head)
        commits = CommitStore(self.repository.root)
        parent = commits.read(parent_hash)
        content = self.normalizer.normalize(self.provider.export_docx())
        blobs = BlobStore(self.repository.root)
        blob_hash = blobs.save(content)
        modified_time = self.provider.modified_time()
        config = self.repository.read_config()
        if blob_hash == parent.blob:
            self.repository.write_config(
                RepoConfig(
                    document_id=config.document_id,
                    repository_name=config.repository_name,
                    format_version=config.format_version,
                    modified_time=modified_time,
                )
            )
            return OperationResult(False, parent.hash, "Nada para commitar.")
        draft = Commit(
            hash="",
            parent=parent.hash,
            blob=blob_hash,
            message=message,
            author=self.author,
            timestamp=utc_timestamp(self.clock.now()),
        )
        commit = Commit(hash=commit_hash(draft), **draft.without_hash())
        commits.save(commit)
        self.repository.write_branch(head, commit.hash)
        self.repository.write_config(
            RepoConfig(
                document_id=config.document_id,
                repository_name=config.repository_name,
                format_version=config.format_version,
                modified_time=modified_time,
            )
        )
        return OperationResult(True, commit.hash, "Commit criado.")
