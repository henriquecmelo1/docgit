"""Offline tests for the disposable Google Drive spike."""

from __future__ import annotations

import io
import zipfile

import pytest
from scripts.google_spike import (
    SpikeError,
    fallback_hash,
    normalize_docx,
    normalized_hash,
)


def _docx(core_xml: bytes, *, reverse: bool = False) -> bytes:
    entries = [
        ("word/styles.xml", b"<styles><style name='body'/></styles>"),
        ("docProps/core.xml", core_xml),
        ("word/document.xml", b"<document><p>Hello</p></document>"),
    ]
    if reverse:
        entries.reverse()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return output.getvalue()


def test_normalization_removes_volatile_core_properties_and_sorts_entries() -> None:
    first = _docx(
        b"<core><created>one</created><modified>one</modified>"
        b"<lastModifiedBy>one</lastModifiedBy><title>CV</title></core>"
    )
    second = _docx(
        b"<core><title>CV</title><lastModifiedBy>two</lastModifiedBy>"
        b"<modified>two</modified><created>two</created></core>",
        reverse=True,
    )

    assert normalized_hash(first) == normalized_hash(second)
    with zipfile.ZipFile(io.BytesIO(normalize_docx(first))) as archive:
        assert b"<title>CV</title>" in archive.read("docProps/core.xml")


def test_fallback_hash_only_uses_document_and_styles() -> None:
    first = _docx(b"<core><title>CV</title></core>")
    second = _docx(b"<core><title>Other metadata</title></core>", reverse=True)

    assert fallback_hash(first) == fallback_hash(second)


def test_malformed_docx_is_rejected() -> None:
    with pytest.raises(SpikeError, match="valid DOCX"):
        normalized_hash(b"not a zip")


def test_fallback_hash_is_deterministic() -> None:
    content = _docx(b"<core><title>CV</title></core>")

    assert fallback_hash(content) == fallback_hash(content)
