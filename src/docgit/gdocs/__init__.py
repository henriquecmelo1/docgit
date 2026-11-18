"""Google Docs adapter package."""

from docgit.gdocs.factory import GoogleRuntimeFactory
from docgit.gdocs.normalizer import DocxNormalizer
from docgit.gdocs.provider import GoogleDocumentProvider

__all__ = [
    "DocxNormalizer",
    "GoogleDocumentProvider",
    "GoogleRuntimeFactory",
]
