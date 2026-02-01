"""LegacyLipi - Legacy Font PDF Translator.

Translate PDF documents with legacy Indian font encodings to English or other languages.
"""

from importlib.metadata import version

__version__ = version("legacylipi")
__author__ = "Biplob Biswas"

from legacylipi.core.models import (
    BoundingBox,
    DocumentMetadata,
    EncodingDetectionResult,
    FontInfo,
    PDFDocument,
    PDFPage,
    TextBlock,
    TranslationResult,
)

__all__ = [
    "PDFDocument",
    "PDFPage",
    "TextBlock",
    "BoundingBox",
    "FontInfo",
    "DocumentMetadata",
    "EncodingDetectionResult",
    "TranslationResult",
]
