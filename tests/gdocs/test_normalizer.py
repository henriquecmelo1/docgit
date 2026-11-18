"""Tests for Google DOCX normalization."""

from __future__ import annotations

import io
import zipfile

from docgit.gdocs.normalizer import DocxNormalizer


def _docx(core_xml: bytes, *, reverse: bool = False) -> bytes:
    entries = [
        ("docProps/core.xml", core_xml),
        ("word/document.xml", b"<document><p>Hello</p></document>"),
        ("word/styles.xml", b"<styles/>"),
    ]
    if reverse:
        entries.reverse()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return output.getvalue()


def test_normalizer_produces_equal_bytes_for_equal_exports() -> None:
    normalizer = DocxNormalizer()
    first = _docx(
        b"<core><created>one</created><modified>one</modified><title>CV</title></core>"
    )
    second = _docx(
        b"<core><title>CV</title><modified>two</modified><created>two</created></core>",
        reverse=True,
    )

    assert normalizer.normalize(first) == normalizer.normalize(second)


def test_normalizer_removes_volatile_core_properties() -> None:
    normalizer = DocxNormalizer()
    normalized = normalizer.normalize(
        _docx(b"<core><created>one</created><title>CV</title></core>")
    )

    with zipfile.ZipFile(io.BytesIO(normalized)) as archive:
        core_xml = archive.read("docProps/core.xml")

    assert b"created" not in core_xml
    assert b"<title>CV</title>" in core_xml
