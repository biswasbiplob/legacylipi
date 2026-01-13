"""Data models for LegacyLipi.

This module defines all the core data structures used throughout the application.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class DetectionMethod(str, Enum):
    """Method used to detect encoding."""

    FONT_MATCH = "font_match"
    HEURISTIC = "heuristic"
    USER_OVERRIDE = "user_override"
    UNICODE_DETECTED = "unicode_detected"


class OutputFormat(str, Enum):
    """Supported output formats."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"


class TranslationBackend(str, Enum):
    """Supported translation backends."""

    GOOGLE = "google"
    TRANS = "trans"  # translate-shell CLI tool
    MYMEMORY = "mymemory"
    OLLAMA = "ollama"
    OPENAI = "openai"
    DEEPL = "deepl"
    MOCK = "mock"  # For testing


@dataclass
class BoundingBox:
    """Represents a rectangular region on a page."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.y1 - self.y0

    def __repr__(self) -> str:
        return f"BoundingBox({self.x0:.1f}, {self.y0:.1f}, {self.x1:.1f}, {self.y1:.1f})"


@dataclass
class FontInfo:
    """Information about a font used in the PDF."""

    name: str
    encoding: Optional[str] = None
    is_embedded: bool = False
    is_subset: bool = False

    def __hash__(self) -> int:
        return hash((self.name, self.encoding, self.is_embedded))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FontInfo):
            return NotImplemented
        return (
            self.name == other.name
            and self.encoding == other.encoding
            and self.is_embedded == other.is_embedded
        )


@dataclass
class TextBlock:
    """A block of text extracted from a PDF page."""

    raw_text: str
    font_name: Optional[str] = None
    font_size: float = 12.0
    position: Optional[BoundingBox] = None
    detected_encoding: Optional[str] = None
    unicode_text: Optional[str] = None
    confidence: float = 0.0
    translated_text: Optional[str] = None  # Store block-level translation

    @property
    def is_converted(self) -> bool:
        """Check if this block has been converted to Unicode."""
        return self.unicode_text is not None

    @property
    def is_translated(self) -> bool:
        """Check if this block has been translated."""
        return self.translated_text is not None

    @property
    def text(self) -> str:
        """Get the best available text (Unicode if converted, otherwise raw)."""
        return self.unicode_text if self.unicode_text is not None else self.raw_text

    @property
    def display_text(self) -> str:
        """Get best text for display: translated > unicode > raw."""
        if self.translated_text:
            return self.translated_text
        return self.unicode_text if self.unicode_text else self.raw_text


@dataclass
class PDFPage:
    """Represents a single page in a PDF document."""

    page_number: int
    text_blocks: list[TextBlock] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    @property
    def raw_text(self) -> str:
        """Get all raw text from the page."""
        return "\n".join(block.raw_text for block in self.text_blocks)

    @property
    def unicode_text(self) -> str:
        """Get all Unicode text from the page."""
        return "\n".join(block.text for block in self.text_blocks)

    @property
    def fonts_used(self) -> set[str]:
        """Get all font names used on this page."""
        return {block.font_name for block in self.text_blocks if block.font_name}


@dataclass
class DocumentMetadata:
    """Metadata about the PDF document."""

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0


@dataclass
class PDFDocument:
    """Represents a complete PDF document."""

    filepath: Path
    pages: list[PDFPage] = field(default_factory=list)
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    fonts: list[FontInfo] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        """Number of pages in the document."""
        return len(self.pages)

    @property
    def all_fonts(self) -> set[str]:
        """Get all unique font names in the document."""
        fonts = set()
        for page in self.pages:
            fonts.update(page.fonts_used)
        return fonts

    @property
    def raw_text(self) -> str:
        """Get all raw text from the document."""
        return "\n\n".join(page.raw_text for page in self.pages)

    @property
    def unicode_text(self) -> str:
        """Get all Unicode text from the document."""
        return "\n\n".join(page.unicode_text for page in self.pages)


@dataclass
class EncodingDetectionResult:
    """Result of encoding detection for a document or text block."""

    detected_encoding: str
    confidence: float
    method: DetectionMethod
    font_name: Optional[str] = None
    fallback_encodings: list[str] = field(default_factory=list)

    @property
    def is_unicode(self) -> bool:
        """Check if the detected encoding is Unicode."""
        return self.detected_encoding.lower() in (
            "unicode",
            "unicode-devanagari",
            "utf-8",
            "utf8",
        )

    @property
    def is_legacy(self) -> bool:
        """Check if the detected encoding is a legacy encoding."""
        return not self.is_unicode and self.detected_encoding != "unknown"

    @property
    def is_high_confidence(self) -> bool:
        """Check if detection confidence is high (>= 0.9)."""
        return self.confidence >= 0.9

    def __repr__(self) -> str:
        return (
            f"EncodingDetectionResult(encoding={self.detected_encoding!r}, "
            f"confidence={self.confidence:.2f}, method={self.method.value})"
        )


@dataclass
class TranslationResult:
    """Result of translating text."""

    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    translation_backend: TranslationBackend
    chunk_count: int = 1
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if translation was successful."""
        return bool(self.translated_text)

    def __repr__(self) -> str:
        preview = self.translated_text[:50] + "..." if len(self.translated_text) > 50 else self.translated_text
        return (
            f"TranslationResult({self.source_language} -> {self.target_language}, "
            f"backend={self.translation_backend.value}, text={preview!r})"
        )


@dataclass
class ProcessingResult:
    """Complete result of processing a PDF document."""

    document: PDFDocument
    encoding_results: list[EncodingDetectionResult] = field(default_factory=list)
    translation_result: Optional[TranslationResult] = None
    output_path: Optional[Path] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if processing was successful."""
        return len(self.errors) == 0
