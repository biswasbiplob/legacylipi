"""Unicode Converter module for converting legacy-encoded text to Unicode.

This module converts text from legacy Indian font encodings (Shree-Lipi,
Kruti Dev, etc.) to proper Unicode Devanagari.
"""

import unicodedata
from dataclasses import dataclass, field

from legacylipi.core.models import (
    EncodingDetectionResult,
    PDFDocument,
    PDFPage,
    TextBlock,
)
from legacylipi.mappings.loader import (
    MappingLoader,
    MappingLoadError,
    MappingTable,
)


@dataclass
class ConversionResult:
    """Result of converting text from legacy encoding to Unicode."""

    original_text: str
    converted_text: str
    encoding_used: str
    success: bool = True
    warnings: list[str] = field(default_factory=list)
    unmapped_chars: set[str] = field(default_factory=set)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    @property
    def conversion_rate(self) -> float:
        """Calculate the percentage of text that was converted."""
        if not self.original_text:
            return 1.0

        original_chars = set(self.original_text)
        unmapped = len(self.unmapped_chars)
        total = len(original_chars)

        if total == 0:
            return 1.0

        return (total - unmapped) / total


class UnicodeConversionError(Exception):
    """Exception raised when Unicode conversion fails."""

    pass


class UnicodeConverter:
    """Converter for legacy-encoded text to Unicode."""

    def __init__(
        self,
        mapping_loader: MappingLoader | None = None,
        normalize_output: bool = True,
    ):
        """Initialize the Unicode converter.

        Args:
            mapping_loader: Custom mapping loader. Uses default if None.
            normalize_output: Whether to apply NFC normalization to output.
        """
        self._loader = mapping_loader or MappingLoader()
        self._normalize = normalize_output
        self._mapping_cache: dict[str, MappingTable] = {}

    def _get_mapping(self, encoding_name: str) -> MappingTable:
        """Get mapping table for an encoding, with caching.

        Args:
            encoding_name: Name of the encoding.

        Returns:
            MappingTable for the encoding.

        Raises:
            UnicodeConversionError: If mapping cannot be loaded.
        """
        if encoding_name in self._mapping_cache:
            return self._mapping_cache[encoding_name]

        try:
            # Try built-in first
            mapping = self._loader.get_builtin(encoding_name)
            if mapping is None:
                mapping = self._loader.load(encoding_name)

            self._mapping_cache[encoding_name] = mapping
            return mapping
        except MappingLoadError as e:
            raise UnicodeConversionError(f"Cannot load mapping for {encoding_name}: {e}")

    def convert_text(
        self,
        text: str,
        encoding_name: str,
        preserve_unknown: bool = True,
    ) -> ConversionResult:
        """Convert legacy-encoded text to Unicode.

        Args:
            text: The text to convert.
            encoding_name: Name of the source encoding.
            preserve_unknown: If True, keep unmapped characters as-is.
                            If False, replace with Unicode replacement char.

        Returns:
            ConversionResult with converted text and metadata.
        """
        if not text:
            return ConversionResult(
                original_text="",
                converted_text="",
                encoding_used=encoding_name,
            )

        # Handle Unicode input (pass through)
        if encoding_name.lower() in ("unicode", "unicode-devanagari", "utf-8", "utf8"):
            return ConversionResult(
                original_text=text,
                converted_text=text,
                encoding_used=encoding_name,
            )

        try:
            mapping = self._get_mapping(encoding_name)
        except UnicodeConversionError:
            # If no mapping available, return original with warning
            return ConversionResult(
                original_text=text,
                converted_text=text,
                encoding_used=encoding_name,
                success=False,
                warnings=[f"No mapping table available for {encoding_name}"],
            )

        # Perform conversion
        result_text, unmapped = self._apply_mapping(text, mapping, preserve_unknown)

        # Normalize if requested
        if self._normalize and result_text:
            result_text = unicodedata.normalize("NFC", result_text)

        warnings = []
        if unmapped:
            warnings.append(
                f"Found {len(unmapped)} unmapped character(s): {', '.join(repr(c) for c in list(unmapped)[:5])}"
            )

        return ConversionResult(
            original_text=text,
            converted_text=result_text,
            encoding_used=encoding_name,
            warnings=warnings,
            unmapped_chars=unmapped,
        )

    def _apply_mapping(
        self,
        text: str,
        mapping: MappingTable,
        preserve_unknown: bool,
    ) -> tuple[str, set[str]]:
        """Apply mapping table to convert text.

        Args:
            text: Text to convert.
            mapping: Mapping table to use.
            preserve_unknown: Whether to preserve unmapped characters.

        Returns:
            Tuple of (converted_text, set of unmapped characters).
        """
        result = text
        unmapped: set[str] = set()

        # Get all mappings sorted by length (longest first)
        all_mappings = mapping.all_mappings

        # First pass: replace multi-character sequences
        for legacy, unicode_char in all_mappings.items():
            if len(legacy) > 1:
                result = result.replace(legacy, unicode_char)

        # Second pass: replace single characters
        new_result = []
        for char in result:
            if char in all_mappings:
                new_result.append(all_mappings[char])
            elif self._is_passthrough_char(char):
                # Keep ASCII, spaces, punctuation, etc.
                new_result.append(char)
            elif self._is_devanagari(char):
                # Already Unicode Devanagari
                new_result.append(char)
            else:
                unmapped.add(char)
                if preserve_unknown:
                    new_result.append(char)
                else:
                    new_result.append("\ufffd")  # Unicode replacement character

        final_result = "".join(new_result)

        # Apply encoding-specific post-processing
        from legacylipi.core.post_processor import get_post_processor

        post_processor = get_post_processor(mapping.encoding_name)
        final_result = post_processor.process(final_result)

        return final_result, unmapped

    def _is_passthrough_char(self, char: str) -> bool:
        """Check if character should pass through unchanged.

        Args:
            char: Character to check.

        Returns:
            True if character should be kept as-is.
        """
        # Basic Latin (ASCII printable)
        if 0x20 <= ord(char) <= 0x7E:
            return True

        # Common punctuation and whitespace
        if char in " \t\n\r,.!?;:'\"()[]{}/-+=":
            return True

        # Devanagari punctuation
        if char in "।॥":
            return True

        return False

    def _is_devanagari(self, char: str) -> bool:
        """Check if character is in Unicode Devanagari range.

        Args:
            char: Character to check.

        Returns:
            True if character is Devanagari Unicode.
        """
        code_point = ord(char)
        # Devanagari range
        if 0x0900 <= code_point <= 0x097F:
            return True
        # Devanagari Extended
        if 0xA8E0 <= code_point <= 0xA8FF:
            return True
        # Vedic Extensions
        if 0x1CD0 <= code_point <= 0x1CFF:
            return True
        return False

    def convert_text_block(
        self,
        block: TextBlock,
        encoding_name: str | None = None,
    ) -> TextBlock:
        """Convert a text block from legacy encoding to Unicode.

        Args:
            block: The TextBlock to convert.
            encoding_name: Encoding to use. Uses block's detected encoding if None.

        Returns:
            New TextBlock with unicode_text populated.
        """
        encoding = encoding_name or block.detected_encoding

        if not encoding:
            # No encoding specified, return block unchanged
            return TextBlock(
                raw_text=block.raw_text,
                font_name=block.font_name,
                font_size=block.font_size,
                position=block.position,
                detected_encoding=block.detected_encoding,
                unicode_text=block.raw_text,  # Assume it's already readable
                confidence=block.confidence,
            )

        result = self.convert_text(block.raw_text, encoding)

        return TextBlock(
            raw_text=block.raw_text,
            font_name=block.font_name,
            font_size=block.font_size,
            position=block.position,
            detected_encoding=encoding,
            unicode_text=result.converted_text,
            confidence=result.conversion_rate,
        )

    def convert_page(
        self,
        page: PDFPage,
        encoding_name: str | None = None,
        page_encoding: EncodingDetectionResult | None = None,
    ) -> PDFPage:
        """Convert all text blocks on a page.

        Args:
            page: The PDFPage to convert.
            encoding_name: Encoding to use for all blocks.
            page_encoding: Detection result for this page.

        Returns:
            New PDFPage with converted text blocks.
        """
        # Determine encoding to use
        encoding = encoding_name
        if not encoding and page_encoding:
            encoding = page_encoding.detected_encoding

        converted_blocks = []
        for block in page.text_blocks:
            block_encoding = encoding or block.detected_encoding
            converted_block = self.convert_text_block(block, block_encoding)
            converted_blocks.append(converted_block)

        return PDFPage(
            page_number=page.page_number,
            text_blocks=converted_blocks,
            width=page.width,
            height=page.height,
        )

    def convert_document(
        self,
        document: PDFDocument,
        encoding_name: str | None = None,
        page_encodings: dict[int, EncodingDetectionResult] | None = None,
    ) -> PDFDocument:
        """Convert all text in a document.

        Args:
            document: The PDFDocument to convert.
            encoding_name: Encoding to use for all pages (overrides per-page).
            page_encodings: Dictionary mapping page numbers to encoding results.

        Returns:
            New PDFDocument with converted pages.
        """
        converted_pages = []

        for page in document.pages:
            page_encoding = None
            if page_encodings:
                page_encoding = page_encodings.get(page.page_number)

            converted_page = self.convert_page(
                page,
                encoding_name=encoding_name,
                page_encoding=page_encoding,
            )
            converted_pages.append(converted_page)

        return PDFDocument(
            filepath=document.filepath,
            pages=converted_pages,
            metadata=document.metadata,
            fonts=document.fonts,
        )


def convert_to_unicode(
    text: str,
    encoding_name: str,
    preserve_unknown: bool = True,
) -> str:
    """Convenience function to convert legacy-encoded text to Unicode.

    Args:
        text: The text to convert.
        encoding_name: Name of the source encoding.
        preserve_unknown: Whether to keep unmapped characters.

    Returns:
        Converted Unicode text.
    """
    converter = UnicodeConverter()
    result = converter.convert_text(text, encoding_name, preserve_unknown)
    return result.converted_text
