"""Tests for the mocked Google DocumentProvider boundary."""

from __future__ import annotations

from googleapiclient.http import MediaIoBaseUpload

from docgit.gdocs.provider import GoogleDocumentProvider


class _Request:
    def __init__(self, response: object) -> None:
        self.response = response

    def execute(self) -> object:
        return self.response


class _Files:
    def __init__(self) -> None:
        self.last_export: dict[str, object] = {}
        self.last_update: dict[str, object] = {}

    def get(self, **kwargs: object) -> _Request:
        assert kwargs["fileId"] == "document-id"
        assert kwargs["fields"] == "modifiedTime,headRevisionId"
        return _Request({"modifiedTime": "2026-11-17T12:00:00Z"})

    def export(self, **kwargs: object) -> _Request:
        self.last_export = kwargs
        return _Request(b"docx-content")

    def update(self, **kwargs: object) -> _Request:
        self.last_update = kwargs
        return _Request({"id": "document-id"})


class _Service:
    def __init__(self) -> None:
        self._files = _Files()

    def files(self) -> _Files:
        return self._files


def test_provider_exports_updates_and_reads_modified_time() -> None:
    service = _Service()
    provider = GoogleDocumentProvider("document-id", service)

    assert provider.export_docx() == b"docx-content"
    provider.replace_content(b"replacement")

    assert provider.modified_time() == "2026-11-17T12:00:00Z"
    assert service.files().last_export["mimeType"].endswith("wordprocessingml.document")
    assert service.files().last_update["fileId"] == "document-id"
    assert isinstance(service.files().last_update["media_body"], MediaIoBaseUpload)
