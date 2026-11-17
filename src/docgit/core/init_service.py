"""Repository initialization use case."""

from pathlib import Path

from docgit.core.blobs import BlobStore
from docgit.core.clock import SystemClock
from docgit.core.commits import CommitStore
from docgit.core.exceptions import RepositoryAlreadyExistsError
from docgit.core.hashing import commit_hash, utc_timestamp
from docgit.core.models import Commit, RepoConfig
from docgit.core.ports import Clock, DocumentProvider, IdentityNormalizer, Normalizer
from docgit.core.refs import Repository

INITIAL_COMMIT_MESSAGE = "Initial commit"


class InitService:
    """Initialize a repository from the current document."""

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

    def initialize(self, document_id: str, repository_name: str) -> Commit:
        """Create the initial branch, commit and workspace configuration."""
        if self.repository.root.exists():
            raise RepositoryAlreadyExistsError("O repositório docgit já existe.")
        self.repository.create_layout()
        blob_store = BlobStore(self.repository.root)
        commit_store = CommitStore(self.repository.root)
        content = self.normalizer.normalize(self.provider.export_docx())
        blob_hash = blob_store.save(content)
        draft = Commit(
            hash="",
            parent=None,
            blob=blob_hash,
            message=INITIAL_COMMIT_MESSAGE,
            author=self.author,
            timestamp=utc_timestamp(self.clock.now()),
        )
        commit = Commit(hash=commit_hash(draft), **draft.without_hash())
        commit_store.save(commit)
        self.repository.write_branch("main", commit.hash)
        self.repository.write_head("main")
        self.repository.write_config(
            RepoConfig(
                document_id=document_id,
                repository_name=repository_name,
                format_version=1,
                modified_time=self.provider.modified_time(),
            )
        )
        return commit
