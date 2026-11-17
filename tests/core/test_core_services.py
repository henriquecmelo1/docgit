from datetime import UTC, datetime
from pathlib import Path

import pytest

from docgit.core.branch_service import BranchService
from docgit.core.checkout_service import CheckoutService
from docgit.core.commit_service import CommitService
from docgit.core.commits import CommitStore
from docgit.core.exceptions import (
    AmbiguousCommitError,
    BranchAlreadyExistsError,
    InvalidBranchNameError,
    UncommittedChangesError,
)
from docgit.core.hashing import canonical_json, resolve_commit_hash, sha256_bytes
from docgit.core.init_service import InitService
from docgit.core.log_service import LogService
from docgit.core.ports import IdentityNormalizer


class FixedClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


class FakeProvider:
    def __init__(self, content: bytes = b"initial") -> None:
        self.content = content
        self.version = 1
        self.fail_replace = False

    def export_docx(self) -> bytes:
        return self.content

    def replace_content(self, docx: bytes) -> None:
        if self.fail_replace:
            raise RuntimeError("replacement failed")
        self.content = docx
        self.version += 1

    def modified_time(self) -> str:
        return f"version-{self.version}"


def initialize(tmp_path: Path, provider: FakeProvider) -> None:
    InitService(
        tmp_path,
        provider,
        "Henri <henri@example.com>",
        FixedClock(),
        IdentityNormalizer(),
    ).initialize("document-id", tmp_path.name)


def test_canonical_json_and_hash_are_deterministic() -> None:
    assert canonical_json({"b": 2, "a": "á"}) == b'{"a":"\xc3\xa1","b":2}'
    assert sha256_bytes(b"same") == sha256_bytes(b"same")


def test_init_creates_initial_commit_and_layout(tmp_path: Path) -> None:
    provider = FakeProvider()

    initialize(tmp_path, provider)

    root = tmp_path / ".docgit"
    assert (root / "HEAD").read_text(encoding="utf-8").strip() == "main"
    assert (root / "refs" / "heads" / "main").is_file()
    assert len(list((root / "commits").glob("*.json"))) == 1
    assert len(list((root / "blobs").glob("*.docx"))) == 1


def test_commit_creates_new_commit_and_noop_does_not_advance(tmp_path: Path) -> None:
    provider = FakeProvider()
    initialize(tmp_path, provider)
    service = CommitService(
        tmp_path,
        provider,
        "Henri <henri@example.com>",
        FixedClock(),
        IdentityNormalizer(),
    )
    initial = CommitStore(tmp_path / ".docgit").all_hashes()

    unchanged = service.create("No change")
    provider.content = b"changed"
    changed = service.create("Update document")

    assert not unchanged.changed
    assert changed.changed
    assert changed.commit_hash not in initial
    assert len(CommitStore(tmp_path / ".docgit").all_hashes()) == 2


def test_branch_and_log_preserve_history(tmp_path: Path) -> None:
    provider = FakeProvider()
    initialize(tmp_path, provider)
    commit_service = CommitService(
        tmp_path,
        provider,
        "Henri <henri@example.com>",
        FixedClock(),
        IdentityNormalizer(),
    )
    provider.content = b"second"
    commit_service.create("Second")

    branch_service = BranchService(tmp_path)
    branch_service.create("feature")
    with pytest.raises(BranchAlreadyExistsError):
        branch_service.create("feature")

    history = LogService(tmp_path).history()
    assert [item.message for item in history] == ["Second", "Initial commit"]
    assert branch_service.list() == [("feature", False), ("main", True)]


def test_checkout_refuses_dirty_workspace_and_force_discards_it(
    tmp_path: Path,
) -> None:
    provider = FakeProvider()
    initialize(tmp_path, provider)
    commit_service = CommitService(
        tmp_path,
        provider,
        "Henri <henri@example.com>",
        FixedClock(),
        IdentityNormalizer(),
    )
    provider.content = b"feature"
    commit_service.create("Feature content")
    BranchService(tmp_path).create("feature")

    provider.content = b"uncommitted"
    provider.version += 1
    with pytest.raises(UncommittedChangesError):
        CheckoutService(tmp_path, provider).checkout("feature")
    assert provider.content == b"uncommitted"

    CheckoutService(tmp_path, provider).checkout("feature", force=True)
    assert provider.content == b"feature"
    assert (tmp_path / ".docgit" / "HEAD").read_text(
        encoding="utf-8"
    ).strip() == "feature"


def test_checkout_failure_preserves_head(tmp_path: Path) -> None:
    provider = FakeProvider()
    initialize(tmp_path, provider)
    BranchService(tmp_path).create("feature")
    provider.fail_replace = True

    with pytest.raises(RuntimeError):
        CheckoutService(tmp_path, provider).checkout("feature")

    assert (tmp_path / ".docgit" / "HEAD").read_text(encoding="utf-8").strip() == "main"


def test_ambiguous_commit_prefix_is_rejected() -> None:
    with pytest.raises(AmbiguousCommitError):
        resolve_commit_hash("abc", ["abc111", "abc222"])


def test_branch_path_traversal_is_rejected(tmp_path: Path) -> None:
    initialize(tmp_path, FakeProvider())

    with pytest.raises(InvalidBranchNameError):
        BranchService(tmp_path).create("../outside")
