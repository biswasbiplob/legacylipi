"""Tests for data models."""

from pathlib import Path

from legacylipi.core.models import (
    BoundingBox,
    DetectionMethod,
    DocumentMetadata,
    EncodingDetectionResult,
    FontInfo,
    OutputFormat,
    PDFDocument,
    PDFPage,
    ProcessingResult,
    TextBlock,
    TranslationBackend,
    TranslationResult,
)


class TestBoundingBox:
    """Tests for BoundingBox model."""

    def test_create_bounding_box(self):
        """Test creating a bounding box."""
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0)
        assert bbox.x0 == 10.0
        assert bbox.y0 == 20.0
        assert bbox.x1 == 100.0
        assert bbox.y1 == 50.0

    def test_width_calculation(self):
        """Test width property."""
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0)
        assert bbox.width == 90.0

    def test_height_calculation(self):
        """Test height property."""
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0)
        assert bbox.height == 30.0

    def test_repr(self):
        """Test string representation."""
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0)
        assert "10.0" in repr(bbox)
        assert "BoundingBox" in repr(bbox)


class TestFontInfo:
    """Tests for FontInfo model."""

    def test_create_font_info(self):
        """Test creating font info."""
        font = FontInfo(name="Shree-Dev-0714", encoding="custom", is_embedded=True)
        assert font.name == "Shree-Dev-0714"
        assert font.encoding == "custom"
        assert font.is_embedded is True

    def test_font_info_defaults(self):
        """Test default values."""
        font = FontInfo(name="Arial")
        assert font.encoding is None
        assert font.is_embedded is False
        assert font.is_subset is False

    def test_font_info_hash(self):
        """Test that FontInfo is hashable."""
        font1 = FontInfo(name="Arial", encoding="utf-8", is_embedded=True)
        font2 = FontInfo(name="Arial", encoding="utf-8", is_embedded=True)
        assert hash(font1) == hash(font2)

    def test_font_info_equality(self):
        """Test FontInfo equality."""
        font1 = FontInfo(name="Arial", encoding="utf-8", is_embedded=True)
        font2 = FontInfo(name="Arial", encoding="utf-8", is_embedded=True)
        font3 = FontInfo(name="Times", encoding="utf-8", is_embedded=True)
        assert font1 == font2
        assert font1 != font3

    def test_font_info_in_set(self):
        """Test using FontInfo in a set."""
        font1 = FontInfo(name="Arial")
        font2 = FontInfo(name="Arial")
        font3 = FontInfo(name="Times")
        fonts = {font1, font2, font3}
        assert len(fonts) == 2


class TestTextBlock:
    """Tests for TextBlock model."""

    def test_create_text_block(self):
        """Test creating a text block."""
        block = TextBlock(
            raw_text="Hello",
            font_name="Arial",
            font_size=12.0,
        )
        assert block.raw_text == "Hello"
        assert block.font_name == "Arial"
        assert block.font_size == 12.0

    def test_text_block_not_converted(self):
        """Test text block before conversion."""
        block = TextBlock(raw_text="´ÖÆüÖ¸üÖÂ™Òü")
        assert block.is_converted is False
        assert block.text == "´ÖÆüÖ¸üÖÂ™Òü"

    def test_text_block_converted(self):
        """Test text block after conversion."""
        block = TextBlock(
            raw_text="´ÖÆüÖ¸üÖÂ™Òü",
            unicode_text="महाराष्ट्र",
        )
        assert block.is_converted is True
        assert block.text == "महाराष्ट्र"

    def test_text_block_with_position(self):
        """Test text block with bounding box."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=20)
        block = TextBlock(raw_text="Test", position=bbox)
        assert block.position is not None
        assert block.position.width == 100


class TestPDFPage:
    """Tests for PDFPage model."""

    def test_create_page(self):
        """Test creating a PDF page."""
        page = PDFPage(page_number=1, width=612.0, height=792.0)
        assert page.page_number == 1
        assert page.width == 612.0
        assert page.height == 792.0

    def test_page_raw_text(self):
        """Test extracting raw text from page."""
        blocks = [
            TextBlock(raw_text="Line 1"),
            TextBlock(raw_text="Line 2"),
        ]
        page = PDFPage(page_number=1, text_blocks=blocks)
        assert page.raw_text == "Line 1\nLine 2"

    def test_page_unicode_text(self):
        """Test extracting Unicode text from page."""
        blocks = [
            TextBlock(raw_text="raw1", unicode_text="unicode1"),
            TextBlock(raw_text="raw2", unicode_text="unicode2"),
        ]
        page = PDFPage(page_number=1, text_blocks=blocks)
        assert page.unicode_text == "unicode1\nunicode2"

    def test_page_fonts_used(self):
        """Test getting fonts used on page."""
        blocks = [
            TextBlock(raw_text="A", font_name="Arial"),
            TextBlock(raw_text="B", font_name="Times"),
            TextBlock(raw_text="C", font_name="Arial"),
        ]
        page = PDFPage(page_number=1, text_blocks=blocks)
        assert page.fonts_used == {"Arial", "Times"}


class TestPDFDocument:
    """Tests for PDFDocument model."""

    def test_create_document(self):
        """Test creating a PDF document."""
        doc = PDFDocument(filepath=Path("/test/doc.pdf"))
        assert doc.filepath == Path("/test/doc.pdf")
        assert doc.page_count == 0

    def test_document_page_count(self):
        """Test page count property."""
        pages = [
            PDFPage(page_number=1),
            PDFPage(page_number=2),
            PDFPage(page_number=3),
        ]
        doc = PDFDocument(filepath=Path("/test/doc.pdf"), pages=pages)
        assert doc.page_count == 3

    def test_document_all_fonts(self):
        """Test getting all fonts from document."""
        pages = [
            PDFPage(
                page_number=1,
                text_blocks=[TextBlock(raw_text="A", font_name="Arial")],
            ),
            PDFPage(
                page_number=2,
                text_blocks=[TextBlock(raw_text="B", font_name="Times")],
            ),
        ]
        doc = PDFDocument(filepath=Path("/test/doc.pdf"), pages=pages)
        assert doc.all_fonts == {"Arial", "Times"}

    def test_document_with_metadata(self):
        """Test document with metadata."""
        metadata = DocumentMetadata(
            title="Test Document",
            author="Test Author",
            page_count=10,
        )
        doc = PDFDocument(filepath=Path("/test/doc.pdf"), metadata=metadata)
        assert doc.metadata.title == "Test Document"
        assert doc.metadata.author == "Test Author"


class TestEncodingDetectionResult:
    """Tests for EncodingDetectionResult model."""

    def test_create_detection_result(self):
        """Test creating an encoding detection result."""
        result = EncodingDetectionResult(
            detected_encoding="shree-lipi-0714",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )
        assert result.detected_encoding == "shree-lipi-0714"
        assert result.confidence == 0.95
        assert result.method == DetectionMethod.FONT_MATCH

    def test_is_unicode(self):
        """Test Unicode detection."""
        unicode_result = EncodingDetectionResult(
            detected_encoding="unicode-devanagari",
            confidence=1.0,
            method=DetectionMethod.UNICODE_DETECTED,
        )
        legacy_result = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.9,
            method=DetectionMethod.FONT_MATCH,
        )
        assert unicode_result.is_unicode is True
        assert legacy_result.is_unicode is False

    def test_is_legacy(self):
        """Test legacy encoding detection."""
        legacy_result = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.9,
            method=DetectionMethod.FONT_MATCH,
        )
        unknown_result = EncodingDetectionResult(
            detected_encoding="unknown",
            confidence=0.0,
            method=DetectionMethod.HEURISTIC,
        )
        assert legacy_result.is_legacy is True
        assert unknown_result.is_legacy is False

    def test_is_high_confidence(self):
        """Test confidence threshold."""
        high_conf = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )
        low_conf = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.7,
            method=DetectionMethod.HEURISTIC,
        )
        assert high_conf.is_high_confidence is True
        assert low_conf.is_high_confidence is False

    def test_repr(self):
        """Test string representation."""
        result = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )
        repr_str = repr(result)
        assert "shree-lipi" in repr_str
        assert "0.95" in repr_str


class TestTranslationResult:
    """Tests for TranslationResult model."""

    def test_create_translation_result(self):
        """Test creating a translation result."""
        result = TranslationResult(
            source_text="महाराष्ट्र",
            translated_text="Maharashtra",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.GOOGLE,
        )
        assert result.source_text == "महाराष्ट्र"
        assert result.translated_text == "Maharashtra"
        assert result.translation_backend == TranslationBackend.GOOGLE

    def test_translation_success(self):
        """Test success property."""
        success = TranslationResult(
            source_text="test",
            translated_text="translated",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
        )
        failure = TranslationResult(
            source_text="test",
            translated_text="",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
        )
        assert success.success is True
        assert failure.success is False

    def test_translation_with_warnings(self):
        """Test translation with warnings."""
        result = TranslationResult(
            source_text="test",
            translated_text="translated",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
            warnings=["Low confidence translation"],
        )
        assert len(result.warnings) == 1


class TestProcessingResult:
    """Tests for ProcessingResult model."""

    def test_create_processing_result(self):
        """Test creating a processing result."""
        doc = PDFDocument(filepath=Path("/test/doc.pdf"))
        result = ProcessingResult(document=doc)
        assert result.document == doc
        assert result.success is True

    def test_processing_result_with_errors(self):
        """Test processing result with errors."""
        doc = PDFDocument(filepath=Path("/test/doc.pdf"))
        result = ProcessingResult(
            document=doc,
            errors=["Failed to parse page 5"],
        )
        assert result.success is False

    def test_processing_result_with_translation(self):
        """Test processing result with translation."""
        doc = PDFDocument(filepath=Path("/test/doc.pdf"))
        translation = TranslationResult(
            source_text="test",
            translated_text="translated",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
        )
        result = ProcessingResult(
            document=doc,
            translation_result=translation,
        )
        assert result.translation_result is not None
        assert result.translation_result.translated_text == "translated"


class TestEnums:
    """Tests for enum types."""

    def test_detection_method_values(self):
        """Test DetectionMethod enum values."""
        assert DetectionMethod.FONT_MATCH.value == "font_match"
        assert DetectionMethod.HEURISTIC.value == "heuristic"
        assert DetectionMethod.USER_OVERRIDE.value == "user_override"

    def test_output_format_values(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.PDF.value == "pdf"

    def test_translation_backend_values(self):
        """Test TranslationBackend enum values."""
        assert TranslationBackend.GOOGLE.value == "google"
        assert TranslationBackend.OLLAMA.value == "ollama"
        assert TranslationBackend.MOCK.value == "mock"
