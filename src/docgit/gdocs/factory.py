"""Google-backed runtime factory for the CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docgit.core.author import git_author
from docgit.core.clock import SystemClock
from docgit.gdocs.auth import authenticate, document_id
from docgit.gdocs.normalizer import DocxNormalizer
from docgit.gdocs.provider import GoogleDocumentProvider

if TYPE_CHECKING:
    from docgit.cli import Runtime


class GoogleRuntimeFactory:
    """Create core runtimes backed by Google Drive."""

    def create(self, document_id_or_url: str) -> Runtime:
        """Authenticate and create the runtime dependencies."""
        from docgit.cli import Runtime

        credentials = authenticate()
        try:
            from googleapiclient.discovery import build
        except ImportError as error:
            raise RuntimeError(
                "Dependências do Google não estão instaladas."
            ) from error
        service = build("drive", "v3", credentials=credentials)
        return Runtime(
            provider=GoogleDocumentProvider(document_id(document_id_or_url), service),
            author=git_author(),
            clock=SystemClock(),
            normalizer=DocxNormalizer(),
        )
