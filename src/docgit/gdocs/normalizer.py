"""Deterministic DOCX normalization for Google exports."""

from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree

_VOLATILE_CORE_TAGS = frozenset({"lastModifiedBy", "created", "modified"})


class DocxNormalizer:
    """Normalize Google DOCX exports into deterministic ZIP bytes."""

    def normalize(self, docx: bytes) -> bytes:
        """Remove volatile metadata, sort entries and repackage as ZIP."""
        try:
            source = zipfile.ZipFile(io.BytesIO(docx))
        except zipfile.BadZipFile as error:
            raise ValueError(
                "O conteúdo exportado não é um arquivo DOCX válido."
            ) from error

        entries: list[tuple[str, bytes]] = []
        with source:
            for info in source.infolist():
                content = source.read(info)
                if info.filename == "docProps/core.xml":
                    content = self._normalize_core_xml(content)
                entries.append((info.filename, content))

        output = io.BytesIO()
        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as target:
            for filename, content in sorted(entries):
                info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 0
                info.external_attr = 0
                target.writestr(info, content)
        return output.getvalue()

    def _normalize_core_xml(self, content: bytes) -> bytes:
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError:
            return content
        for parent in root.iter():
            for child in list(parent):
                local_name = child.tag.rsplit("}", 1)[-1]
                if local_name in _VOLATILE_CORE_TAGS:
                    parent.remove(child)
        return ElementTree.tostring(root, encoding="utf-8")
