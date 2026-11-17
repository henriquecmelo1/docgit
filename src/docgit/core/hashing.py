"""Deterministic serialization and content addressing."""

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from docgit.core.exceptions import AmbiguousCommitError, CommitNotFoundError
from docgit.core.models import Commit


def canonical_json(value: Any) -> bytes:
    """Serialize JSON deterministically as UTF-8 bytes."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return a SHA-256 hexadecimal digest."""
    return hashlib.sha256(value).hexdigest()


def commit_hash(commit: Commit) -> str:
    """Calculate a commit hash without including its hash field."""
    return sha256_bytes(canonical_json(commit.without_hash()))


def utc_timestamp(value: datetime) -> str:
    """Format a datetime as an ISO-8601 UTC timestamp with ``Z``."""
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def resolve_commit_hash(
    reference: str,
    hashes: Iterable[str],
) -> str:
    """Resolve a complete hash or an unambiguous prefix."""
    available = sorted(hashes)
    if reference in available:
        return reference
    matches = [value for value in available if value.startswith(reference)]
    if not matches:
        raise CommitNotFoundError(f"Commit não encontrado: {reference}")
    if len(matches) > 1:
        raise AmbiguousCommitError(f"Referência de commit ambígua: {reference}")
    return matches[0]
