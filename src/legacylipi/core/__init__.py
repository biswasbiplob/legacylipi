"""Core modules for LegacyLipi."""

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
from legacylipi.core.pdf_parser import PDFParseError, PDFParser, parse_pdf
from legacylipi.core.encoding_detector import (
    EncodingDetector,
    LegacyFontPattern,
    detect_encoding,
)
from legacylipi.core.unicode_converter import (
    ConversionResult,
    UnicodeConversionError,
    UnicodeConverter,
    convert_to_unicode,
)
from legacylipi.core.translator import (
    TranslationEngine,
    TranslationError,
    TranslationConfig,
    create_translator,
)
from legacylipi.core.output_generator import (
    OutputGenerator,
    OutputMetadata,
    generate_output,
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
    "PDFParser",
    "PDFParseError",
    "parse_pdf",
    "EncodingDetector",
    "LegacyFontPattern",
    "detect_encoding",
    "UnicodeConverter",
    "UnicodeConversionError",
    "ConversionResult",
    "convert_to_unicode",
    "TranslationEngine",
    "TranslationError",
    "TranslationConfig",
    "create_translator",
    "OutputGenerator",
    "OutputMetadata",
    "generate_output",
]
