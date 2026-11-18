"""Google Drive implementation of DocumentProvider."""

from __future__ import annotations

import io
from typing import Any

from docgit.core.exceptions import ProviderError

DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


class GoogleDocumentProvider:
    """Implement document operations with the Google Drive API."""

    def __init__(self, document_id: str, service: Any) -> None:
        self.document_id = document_id
        self.service = service

    def export_docx(self) -> bytes:
        """Export the document as DOCX."""
        try:
            response = (
                self.service.files()
                .export(fileId=self.document_id, mimeType=DOCX_MIME_TYPE)
                .execute()
            )
        except Exception as error:
            raise ProviderError("Não foi possível exportar o documento.") from error
        if not isinstance(response, bytes):
            raise ProviderError("A exportação do Google não retornou conteúdo binário.")
        return response

    def replace_content(self, docx: bytes) -> None:
        """Replace the content of the same Google document."""
        try:
            from googleapiclient.http import MediaIoBaseUpload

            media = MediaIoBaseUpload(
                io.BytesIO(docx),
                mimetype=DOCX_MIME_TYPE,
                resumable=False,
            )
            response = (
                self.service.files()
                .update(
                    fileId=self.document_id,
                    media_body=media,
                    fields="id,webViewLink",
                )
                .execute()
            )
        except Exception as error:
            raise ProviderError(
                "Não foi possível substituir o conteúdo do documento."
            ) from error
        if response.get("id") != self.document_id:
            raise ProviderError("O Google substituiu o conteúdo em outro documento.")

    def modified_time(self) -> str:
        """Return the document's current modification timestamp."""
        try:
            metadata = (
                self.service.files()
                .get(
                    fileId=self.document_id,
                    fields="modifiedTime,headRevisionId",
                )
                .execute()
            )
            return str(metadata["modifiedTime"])
        except Exception as error:
            raise ProviderError(
                "Não foi possível ler o estado do documento."
            ) from error
