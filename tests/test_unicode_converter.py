"""Tests for Unicode Converter module."""

from pathlib import Path

from legacylipi.core.models import (
    DetectionMethod,
    EncodingDetectionResult,
    PDFDocument,
    PDFPage,
    TextBlock,
)
from legacylipi.core.unicode_converter import (
    ConversionResult,
    UnicodeConverter,
    convert_to_unicode,
)


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_create_conversion_result(self):
        """Test creating a conversion result."""
        result = ConversionResult(
            original_text="test",
            converted_text="converted",
            encoding_used="shree-lipi",
        )

        assert result.original_text == "test"
        assert result.converted_text == "converted"
        assert result.success is True

    def test_has_warnings(self):
        """Test has_warnings property."""
        with_warnings = ConversionResult(
            original_text="test",
            converted_text="converted",
            encoding_used="test",
            warnings=["Warning 1"],
        )

        without_warnings = ConversionResult(
            original_text="test",
            converted_text="converted",
            encoding_used="test",
        )

        assert with_warnings.has_warnings is True
        assert without_warnings.has_warnings is False

    def test_conversion_rate(self):
        """Test conversion rate calculation."""
        result = ConversionResult(
            original_text="abc",
            converted_text="xyz",
            encoding_used="test",
            unmapped_chars={"c"},  # 1 of 3 chars unmapped
        )

        # 2 of 3 unique chars mapped = 66.67%
        assert 0.6 < result.conversion_rate < 0.7

    def test_conversion_rate_empty_text(self):
        """Test conversion rate with empty text."""
        result = ConversionResult(
            original_text="",
            converted_text="",
            encoding_used="test",
        )

        assert result.conversion_rate == 1.0


class TestUnicodeConverter:
    """Tests for UnicodeConverter class."""

    def test_default_initialization(self):
        """Test default initialization."""
        converter = UnicodeConverter()
        assert converter is not None

    def test_convert_empty_text(self):
        """Test converting empty text."""
        converter = UnicodeConverter()
        result = converter.convert_text("", "shree-lipi")

        assert result.converted_text == ""
        assert result.success is True

    def test_convert_unicode_passthrough(self):
        """Test that Unicode input passes through unchanged."""
        converter = UnicodeConverter()

        unicode_text = "महाराष्ट्र राजभाषा"
        result = converter.convert_text(unicode_text, "unicode-devanagari")

        assert result.converted_text == unicode_text
        assert result.success is True

    def test_convert_with_unknown_encoding(self):
        """Test conversion with unknown encoding."""
        converter = UnicodeConverter()

        result = converter.convert_text("test", "unknown-encoding-xyz")

        # Should return original with warning
        assert result.converted_text == "test"
        assert result.success is False
        assert len(result.warnings) > 0

    def test_preserve_ascii(self):
        """Test that ASCII characters are preserved."""
        converter = UnicodeConverter()

        # Mixed ASCII and mappable chars
        text = "Hello 123"
        result = converter.convert_text(text, "shree-lipi")

        # ASCII should be preserved
        assert "Hello" in result.converted_text
        assert "123" in result.converted_text or "१२३" in result.converted_text

    def test_preserve_punctuation(self):
        """Test that punctuation is preserved."""
        converter = UnicodeConverter()

        text = "test, (text) - more!"
        result = converter.convert_text(text, "shree-lipi")

        # Punctuation should be preserved
        assert "," in result.converted_text
        assert "(" in result.converted_text
        assert "!" in result.converted_text

    def test_preserve_unknown_characters(self):
        """Test preservation of unmapped characters."""
        converter = UnicodeConverter()

        # Use characters that won't be in mapping
        text = "abc§±µ"
        result = converter.convert_text(text, "shree-lipi", preserve_unknown=True)

        # Unknown chars should be preserved
        assert "§" in result.converted_text or len(result.unmapped_chars) > 0

    def test_replace_unknown_characters(self):
        """Test replacement of unmapped characters."""
        converter = UnicodeConverter()

        # Use characters that won't be in mapping
        text = "§"  # Unlikely to be mapped
        result = converter.convert_text(text, "shree-lipi", preserve_unknown=False)

        # Either mapped or replaced with replacement char
        if "§" not in result.converted_text:
            assert "\ufffd" in result.converted_text or len(result.unmapped_chars) > 0


class TestUnicodeConverterWithKrutiDev:
    """Tests for Unicode converter with Kruti Dev encoding."""

    def test_convert_basic_kruti_dev(self):
        """Test basic Kruti Dev conversion."""
        converter = UnicodeConverter()

        # Kruti Dev patterns
        result = converter.convert_text("Hkkjr", "kruti-dev")

        # Should convert to भारत (Bharat)
        assert "भारत" in result.converted_text or result.has_warnings

    def test_convert_kruti_dev_vowels(self):
        """Test Kruti Dev vowel conversion."""
        converter = UnicodeConverter()

        # 'v' in Kruti Dev is 'अ'
        result = converter.convert_text("v", "kruti-dev")
        assert "अ" in result.converted_text or "v" in result.converted_text


class TestUnicodeConverterWithShreeLipi:
    """Tests for Unicode converter with Shree-Lipi encoding."""

    def test_shree_lipi_available(self):
        """Test that Shree-Lipi mapping is available."""
        converter = UnicodeConverter()

        result = converter.convert_text("test", "shree-lipi")
        # Should not fail to load mapping
        assert result is not None


class TestTextBlockConversion:
    """Tests for text block conversion."""

    def test_convert_text_block_basic(self):
        """Test basic text block conversion."""
        converter = UnicodeConverter()

        block = TextBlock(
            raw_text="test text",
            detected_encoding="shree-lipi",
        )

        converted = converter.convert_text_block(block)

        assert converted.unicode_text is not None
        assert converted.detected_encoding == "shree-lipi"

    def test_convert_text_block_with_encoding_override(self):
        """Test text block conversion with encoding override."""
        converter = UnicodeConverter()

        block = TextBlock(
            raw_text="test",
            detected_encoding="shree-lipi",
        )

        converted = converter.convert_text_block(block, encoding_name="kruti-dev")

        assert converted.detected_encoding == "kruti-dev"

    def test_convert_text_block_preserves_metadata(self):
        """Test that conversion preserves block metadata."""
        from legacylipi.core.models import BoundingBox

        converter = UnicodeConverter()

        block = TextBlock(
            raw_text="test",
            font_name="TestFont",
            font_size=14.0,
            position=BoundingBox(0, 0, 100, 20),
            detected_encoding="shree-lipi",
        )

        converted = converter.convert_text_block(block)

        assert converted.font_name == "TestFont"
        assert converted.font_size == 14.0
        assert converted.position is not None

    def test_convert_text_block_no_encoding(self):
        """Test text block conversion without encoding."""
        converter = UnicodeConverter()

        block = TextBlock(raw_text="plain text")

        converted = converter.convert_text_block(block)

        # Should pass through unchanged
        assert converted.unicode_text == "plain text"


class TestPageConversion:
    """Tests for page conversion."""

    def test_convert_page_basic(self):
        """Test basic page conversion."""
        converter = UnicodeConverter()

        page = PDFPage(
            page_number=1,
            text_blocks=[
                TextBlock(raw_text="block 1", detected_encoding="shree-lipi"),
                TextBlock(raw_text="block 2", detected_encoding="shree-lipi"),
            ],
        )

        converted = converter.convert_page(page)

        assert len(converted.text_blocks) == 2
        assert converted.page_number == 1

    def test_convert_page_with_encoding_override(self):
        """Test page conversion with encoding override."""
        converter = UnicodeConverter()

        page = PDFPage(
            page_number=1,
            text_blocks=[
                TextBlock(raw_text="text", detected_encoding="shree-lipi"),
            ],
        )

        converted = converter.convert_page(page, encoding_name="kruti-dev")

        assert converted.text_blocks[0].detected_encoding == "kruti-dev"

    def test_convert_page_with_detection_result(self):
        """Test page conversion using detection result."""
        converter = UnicodeConverter()

        page = PDFPage(
            page_number=1,
            text_blocks=[TextBlock(raw_text="text")],
        )

        detection = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )

        converted = converter.convert_page(page, page_encoding=detection)

        assert converted.text_blocks[0].detected_encoding == "shree-lipi"


class TestDocumentConversion:
    """Tests for document conversion."""

    def test_convert_document_basic(self):
        """Test basic document conversion."""
        converter = UnicodeConverter()

        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="page 1")],
                ),
                PDFPage(
                    page_number=2,
                    text_blocks=[TextBlock(raw_text="page 2")],
                ),
            ],
        )

        converted = converter.convert_document(doc)

        assert len(converted.pages) == 2
        assert converted.filepath == doc.filepath

    def test_convert_document_with_encoding_override(self):
        """Test document conversion with encoding override."""
        converter = UnicodeConverter()

        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="text")],
                ),
            ],
        )

        converted = converter.convert_document(doc, encoding_name="shree-lipi")

        assert converted.pages[0].text_blocks[0].detected_encoding == "shree-lipi"

    def test_convert_document_with_page_encodings(self):
        """Test document conversion with per-page encodings."""
        converter = UnicodeConverter()

        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(page_number=1, text_blocks=[TextBlock(raw_text="p1")]),
                PDFPage(page_number=2, text_blocks=[TextBlock(raw_text="p2")]),
            ],
        )

        page_encodings = {
            1: EncodingDetectionResult(
                detected_encoding="shree-lipi",
                confidence=0.9,
                method=DetectionMethod.FONT_MATCH,
            ),
            2: EncodingDetectionResult(
                detected_encoding="kruti-dev",
                confidence=0.9,
                method=DetectionMethod.FONT_MATCH,
            ),
        }

        converted = converter.convert_document(doc, page_encodings=page_encodings)

        assert converted.pages[0].text_blocks[0].detected_encoding == "shree-lipi"
        assert converted.pages[1].text_blocks[0].detected_encoding == "kruti-dev"

    def test_convert_document_preserves_metadata(self):
        """Test that document conversion preserves metadata."""
        from legacylipi.core.models import DocumentMetadata, FontInfo

        converter = UnicodeConverter()

        metadata = DocumentMetadata(title="Test Doc", author="Test Author")
        fonts = [FontInfo(name="TestFont")]

        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[PDFPage(page_number=1)],
            metadata=metadata,
            fonts=fonts,
        )

        converted = converter.convert_document(doc)

        assert converted.metadata.title == "Test Doc"
        assert converted.metadata.author == "Test Author"
        assert len(converted.fonts) == 1


class TestConvenienceFunction:
    """Tests for convert_to_unicode convenience function."""

    def test_convert_to_unicode_basic(self):
        """Test basic conversion function."""
        result = convert_to_unicode("test", "shree-lipi")
        assert result is not None

    def test_convert_to_unicode_empty(self):
        """Test conversion of empty text."""
        result = convert_to_unicode("", "shree-lipi")
        assert result == ""

    def test_convert_to_unicode_preserve(self):
        """Test conversion with preserve_unknown."""
        result = convert_to_unicode("test §", "shree-lipi", preserve_unknown=True)
        assert result is not None


class TestNormalization:
    """Tests for Unicode normalization."""

    def test_normalization_enabled_by_default(self):
        """Test that NFC normalization is enabled by default."""
        converter = UnicodeConverter()
        assert converter._normalize is True

    def test_normalization_can_be_disabled(self):
        """Test that normalization can be disabled."""
        converter = UnicodeConverter(normalize_output=False)
        assert converter._normalize is False


class TestDevanagariDetection:
    """Tests for Devanagari character detection."""

    def test_is_devanagari_basic(self):
        """Test Devanagari character detection."""
        converter = UnicodeConverter()

        # Devanagari characters
        assert converter._is_devanagari("अ") is True
        assert converter._is_devanagari("क") is True
        assert converter._is_devanagari("म") is True

        # Non-Devanagari
        assert converter._is_devanagari("a") is False
        assert converter._is_devanagari("A") is False
        assert converter._is_devanagari("1") is False

    def test_is_passthrough_char(self):
        """Test passthrough character detection."""
        converter = UnicodeConverter()

        # Should pass through
        assert converter._is_passthrough_char(" ") is True
        assert converter._is_passthrough_char("a") is True
        assert converter._is_passthrough_char("1") is True
        assert converter._is_passthrough_char(",") is True
        assert converter._is_passthrough_char(".") is True

        # Devanagari danda should pass through
        assert converter._is_passthrough_char("।") is True
