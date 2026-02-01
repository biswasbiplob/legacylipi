"""LegacyLipi - Legacy Font PDF Translator.

Translate PDF documents with legacy Indian font encodings to English or other languages.
"""

__version__ = "0.4.0"
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
