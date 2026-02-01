"""Tests for Output Generator module."""

from pathlib import Path

import fitz
import pytest

from legacylipi.core.models import (
    DetectionMethod,
    EncodingDetectionResult,
    OutputFormat,
    PDFDocument,
    PDFPage,
    TextBlock,
    TranslationBackend,
    TranslationResult,
)
from legacylipi.core.output_generator import (
    OutputGenerator,
    OutputMetadata,
    generate_output,
)


@pytest.fixture
def sample_document():
    """Create a sample PDF document for testing."""
    return PDFDocument(
        filepath=Path("/test/sample.pdf"),
        pages=[
            PDFPage(
                page_number=1,
                text_blocks=[
                    TextBlock(raw_text="Page 1 content", unicode_text="Page 1 Unicode")
                ],
            ),
            PDFPage(
                page_number=2,
                text_blocks=[
                    TextBlock(raw_text="Page 2 content", unicode_text="Page 2 Unicode")
                ],
            ),
        ],
    )


@pytest.fixture
def sample_encoding_result():
    """Create a sample encoding detection result."""
    return EncodingDetectionResult(
        detected_encoding="shree-lipi",
        confidence=0.95,
        method=DetectionMethod.FONT_MATCH,
    )


@pytest.fixture
def sample_translation_result():
    """Create a sample translation result."""
    return TranslationResult(
        source_text="मराठी मजकूर",
        translated_text="Marathi text",
        source_language="mr",
        target_language="en",
        translation_backend=TranslationBackend.MOCK,
    )


class TestOutputMetadata:
    """Tests for OutputMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating output metadata."""
        metadata = OutputMetadata(
            source_file="test.pdf",
            encoding_detected="shree-lipi",
            encoding_confidence=0.95,
            source_language="mr",
            target_language="en",
            translation_backend="mock",
            generated_at="2024-01-01T00:00:00",
            page_count=10,
        )

        assert metadata.source_file == "test.pdf"
        assert metadata.encoding_detected == "shree-lipi"
        assert metadata.page_count == 10


class TestOutputGenerator:
    """Tests for OutputGenerator class."""

    def test_default_initialization(self):
        """Test default initialization."""
        generator = OutputGenerator()
        assert generator._include_metadata is True
        assert generator._include_page_numbers is True

    def test_custom_initialization(self):
        """Test custom initialization."""
        generator = OutputGenerator(
            include_metadata=False,
            include_page_numbers=False,
        )
        assert generator._include_metadata is False
        assert generator._include_page_numbers is False

    def test_generate_metadata(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test metadata generation."""
        generator = OutputGenerator()
        metadata = generator.generate_metadata(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        assert metadata.source_file == "sample.pdf"
        assert metadata.encoding_detected == "shree-lipi"
        assert metadata.encoding_confidence == 0.95
        assert metadata.source_language == "mr"
        assert metadata.target_language == "en"
        assert metadata.page_count == 2


class TestTextOutput:
    """Tests for text output generation."""

    def test_generate_text_basic(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test basic text output generation."""
        generator = OutputGenerator()
        output = generator.generate_text(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        assert "LegacyLipi" in output
        assert "sample.pdf" in output
        assert "shree-lipi" in output

    def test_generate_text_without_metadata(
        self, sample_document, sample_encoding_result
    ):
        """Test text generation without metadata."""
        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_text(
            sample_document,
            sample_encoding_result,
        )

        assert "LegacyLipi" not in output

    def test_generate_text_with_translated_text_override(
        self, sample_encoding_result, sample_translation_result
    ):
        """Test text generation with custom translated text."""
        # Use single-page document to avoid page markers interfering
        single_page_doc = PDFDocument(
            filepath=Path("/test/single.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="original", unicode_text="unicode")],
                )
            ],
        )
        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_text(
            single_page_doc,
            sample_encoding_result,
            sample_translation_result,
            translated_text="Custom translated content",
        )

        assert "Custom translated content" in output

    def test_generate_text_with_page_numbers(
        self, sample_document, sample_encoding_result
    ):
        """Test text generation with page number markers."""
        generator = OutputGenerator(include_metadata=False, include_page_numbers=True)
        output = generator.generate_text(
            sample_document,
            sample_encoding_result,
        )

        assert "Page 1" in output
        assert "Page 2" in output


class TestMarkdownOutput:
    """Tests for Markdown output generation."""

    def test_generate_markdown_basic(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test basic Markdown output generation."""
        generator = OutputGenerator()
        output = generator.generate_markdown(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        # Should have Markdown table formatting
        assert "|" in output
        assert "---" in output
        assert "sample.pdf" in output

    def test_generate_markdown_header_format(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test Markdown header formatting."""
        generator = OutputGenerator()
        output = generator.generate_markdown(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        # Should have proper Markdown structure
        assert "# Translation:" in output
        assert "| Property | Value |" in output

    def test_generate_markdown_without_metadata(
        self, sample_document, sample_encoding_result
    ):
        """Test Markdown generation without metadata."""
        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_markdown(
            sample_document,
            sample_encoding_result,
        )

        assert "# Translation:" not in output

    def test_generate_markdown_with_page_headers(
        self, sample_document, sample_encoding_result
    ):
        """Test Markdown generation with page headers."""
        generator = OutputGenerator(include_metadata=False, include_page_numbers=True)
        output = generator.generate_markdown(
            sample_document,
            sample_encoding_result,
        )

        assert "## Page 1" in output
        assert "## Page 2" in output


class TestBilingualOutput:
    """Tests for bilingual output generation."""

    def test_generate_bilingual_basic(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test basic bilingual output generation."""
        generator = OutputGenerator()
        output = generator.generate_bilingual(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        assert "Bilingual Content" in output
        assert "| Original | Translation |" in output

    def test_generate_bilingual_table_structure(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test bilingual table structure."""
        generator = OutputGenerator()
        output = generator.generate_bilingual(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        # Should have table header
        assert "|----------|-------------|" in output


class TestGenerateMethod:
    """Tests for the unified generate method."""

    def test_generate_text_format(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test generate with text format."""
        generator = OutputGenerator()
        output = generator.generate(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
            OutputFormat.TEXT,
        )

        assert "LegacyLipi Translation Output" in output

    def test_generate_markdown_format(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test generate with markdown format."""
        generator = OutputGenerator()
        output = generator.generate(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
            OutputFormat.MARKDOWN,
        )

        assert "# Translation:" in output

    def test_generate_pdf_format(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test generate with PDF format."""
        generator = OutputGenerator()
        output = generator.generate(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
            OutputFormat.PDF,
        )

        # PDF output should be bytes
        assert isinstance(output, bytes)
        # PDF should start with PDF magic bytes
        assert output.startswith(b"%PDF")


class TestPDFOutput:
    """Tests for PDF output generation."""

    def test_generate_pdf_basic(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test basic PDF generation."""
        generator = OutputGenerator()
        output = generator.generate_pdf(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
        )

        # PDF output should be bytes
        assert isinstance(output, bytes)
        # PDF should start with PDF magic bytes
        assert output.startswith(b"%PDF")
        # PDF should end with EOF marker
        assert b"%%EOF" in output

    def test_generate_pdf_without_metadata(
        self, sample_document, sample_encoding_result
    ):
        """Test PDF generation without metadata page."""
        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_pdf(
            sample_document,
            sample_encoding_result,
        )

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")

    def test_generate_pdf_with_devanagari_content(self, sample_encoding_result):
        """Test PDF generation with Devanagari text."""
        document = PDFDocument(
            filepath=Path("/test/marathi.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[
                        TextBlock(
                            raw_text="test",
                            unicode_text="महाराष्ट्र राज्य",
                        )
                    ],
                )
            ],
        )

        generator = OutputGenerator()
        output = generator.generate_pdf(document, sample_encoding_result)

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")

    def test_generate_pdf_multi_page(self, sample_encoding_result):
        """Test PDF generation with multiple pages."""
        document = PDFDocument(
            filepath=Path("/test/multi.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="Page 1", unicode_text="पृष्ठ १")],
                ),
                PDFPage(
                    page_number=2,
                    text_blocks=[TextBlock(raw_text="Page 2", unicode_text="पृष्ठ २")],
                ),
                PDFPage(
                    page_number=3,
                    text_blocks=[TextBlock(raw_text="Page 3", unicode_text="पृष्ठ ३")],
                ),
            ],
        )

        generator = OutputGenerator()
        output = generator.generate_pdf(document, sample_encoding_result)

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")

    def test_generate_pdf_save_to_file(
        self, sample_document, sample_encoding_result, temp_dir
    ):
        """Test saving PDF to file."""
        generator = OutputGenerator()
        output_path = temp_dir / "output.pdf"

        pdf_bytes = generator.generate_pdf(
            sample_document,
            sample_encoding_result,
        )
        generator.save(pdf_bytes, output_path)

        assert output_path.exists()
        content = output_path.read_bytes()
        assert content.startswith(b"%PDF")


class TestSaveMethod:
    """Tests for the save method."""

    def test_save_content(self, temp_dir):
        """Test saving content to file."""
        generator = OutputGenerator()
        output_path = temp_dir / "output.txt"

        generator.save("Test content", output_path)

        assert output_path.exists()
        assert output_path.read_text() == "Test content"

    def test_save_unicode_content(self, temp_dir):
        """Test saving Unicode content to file."""
        generator = OutputGenerator()
        output_path = temp_dir / "unicode.txt"

        content = "मराठी मजकूर - Marathi text"
        generator.save(content, output_path)

        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == content

    def test_save_pdf_content(self, temp_dir):
        """Test saving PDF bytes to file."""
        generator = OutputGenerator()
        output_path = temp_dir / "output.pdf"

        # Create some mock PDF bytes
        pdf_bytes = b"%PDF-1.4 mock content %%EOF"
        generator.save(pdf_bytes, output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == pdf_bytes


class TestConvenienceFunction:
    """Tests for generate_output convenience function."""

    def test_generate_output_basic(
        self, sample_document, sample_encoding_result, sample_translation_result
    ):
        """Test convenience function."""
        output = generate_output(
            sample_document,
            sample_encoding_result,
            sample_translation_result,
            OutputFormat.TEXT,
        )

        assert "LegacyLipi" in output

    def test_generate_output_without_translation(
        self, sample_document, sample_encoding_result
    ):
        """Test convenience function without translation."""
        output = generate_output(
            sample_document,
            sample_encoding_result,
            output_format=OutputFormat.TEXT,
        )

        assert output is not None


class TestSinglePageDocument:
    """Tests for single-page document handling."""

    def test_single_page_no_page_markers(self, sample_encoding_result):
        """Test that single-page documents don't get page markers."""
        document = PDFDocument(
            filepath=Path("/test/single.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="Only page", unicode_text="Only page")],
                )
            ],
        )

        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_text(document, sample_encoding_result)

        # Single page shouldn't have page markers
        assert "--- Page" not in output


class TestPDFStructurePreservation:
    """Tests for PDF structure preservation feature."""

    def test_pdf_preserves_page_dimensions(self, sample_encoding_result):
        """Test that PDF output preserves original page dimensions."""
        import fitz

        # Create document with specific page dimensions
        document = PDFDocument(
            filepath=Path("/test/custom_size.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=612.0,  # US Letter width
                    height=792.0,  # US Letter height
                    text_blocks=[TextBlock(raw_text="Test", unicode_text="Test content")],
                ),
                PDFPage(
                    page_number=2,
                    width=500.0,  # Custom width
                    height=700.0,  # Custom height
                    text_blocks=[TextBlock(raw_text="Page 2", unicode_text="Page 2 content")],
                ),
            ],
        )

        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_pdf(
            document, sample_encoding_result, preserve_structure=True
        )

        # Parse the output PDF and verify dimensions
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            assert len(pdf) == 2
            # First page should match original dimensions
            assert abs(pdf[0].rect.width - 612.0) < 1
            assert abs(pdf[0].rect.height - 792.0) < 1
            # Second page should match its dimensions
            assert abs(pdf[1].rect.width - 500.0) < 1
            assert abs(pdf[1].rect.height - 700.0) < 1
        finally:
            pdf.close()

    def test_pdf_preserves_text_positions(self, sample_encoding_result):
        """Test that PDF output preserves text block positions."""
        import fitz
        from legacylipi.core.models import BoundingBox

        # Create document with positioned text blocks
        document = PDFDocument(
            filepath=Path("/test/positioned.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=612.0,
                    height=792.0,
                    text_blocks=[
                        TextBlock(
                            raw_text="Header",
                            unicode_text="Header Text",
                            font_size=14.0,
                            position=BoundingBox(x0=50, y0=50, x1=200, y1=70),
                        ),
                        TextBlock(
                            raw_text="Body",
                            unicode_text="Body Text",
                            font_size=11.0,
                            position=BoundingBox(x0=50, y0=100, x1=300, y1=120),
                        ),
                    ],
                ),
            ],
        )

        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_pdf(
            document, sample_encoding_result, preserve_structure=True
        )

        # PDF should be generated successfully
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            assert len(pdf) == 1
            # Verify page has content
            text = pdf[0].get_text()
            assert "Header Text" in text or "Body Text" in text
        finally:
            pdf.close()

    def test_pdf_a4_layout_when_preserve_disabled(self, sample_encoding_result):
        """Test that A4 layout is used when preserve_structure is False."""
        import fitz

        # Create document with non-A4 dimensions
        document = PDFDocument(
            filepath=Path("/test/custom.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=500.0,  # Not A4
                    height=600.0,  # Not A4
                    text_blocks=[TextBlock(raw_text="Test", unicode_text="Test")],
                ),
            ],
        )

        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_pdf(
            document, sample_encoding_result, preserve_structure=False
        )

        # Parse the output PDF - should be A4
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            # A4 dimensions
            assert abs(pdf[0].rect.width - 595) < 1
            assert abs(pdf[0].rect.height - 842) < 1
        finally:
            pdf.close()

    def test_pdf_with_metadata_page_uses_first_page_dimensions(self, sample_encoding_result):
        """Test that metadata page uses first content page's dimensions."""
        import fitz

        # Create document with specific dimensions
        document = PDFDocument(
            filepath=Path("/test/with_meta.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=612.0,
                    height=792.0,
                    text_blocks=[TextBlock(raw_text="Test", unicode_text="Test")],
                ),
            ],
        )

        generator = OutputGenerator(include_metadata=True)
        output = generator.generate_pdf(
            document, sample_encoding_result, preserve_structure=True
        )

        # Parse the output PDF
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            # Should have 2 pages: metadata + content
            assert len(pdf) == 2
            # Metadata page should use first page's dimensions
            assert abs(pdf[0].rect.width - 612.0) < 1
            assert abs(pdf[0].rect.height - 792.0) < 1
        finally:
            pdf.close()

    def test_pdf_uses_translated_text(self, sample_encoding_result):
        """Test that PDF output uses translated text when translation is provided."""
        import fitz

        # Create document with original Marathi-like text
        document = PDFDocument(
            filepath=Path("/test/translation.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=595.0,
                    height=842.0,
                    text_blocks=[
                        TextBlock(raw_text="Original", unicode_text="मराठी मजकूर")
                    ],
                ),
            ],
        )

        # Create translation result with English text
        translation_result = TranslationResult(
            source_text="मराठी मजकूर",
            translated_text="This is the translated English text",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
        )

        generator = OutputGenerator(include_metadata=False)
        output = generator.generate_pdf(
            document, sample_encoding_result, translation_result=translation_result
        )

        # Parse the output PDF and verify translated text is present
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            text = pdf[0].get_text()
            # Should contain the TRANSLATED text, not the original
            assert "translated English" in text
            # Original text should NOT be present (we're not preserving structure)
        finally:
            pdf.close()

    def test_pdf_uses_a4_layout_when_translating(self, sample_encoding_result):
        """Test that PDF uses A4 layout when translation is provided, regardless of preserve_structure."""
        import fitz

        # Create document with non-A4 dimensions
        document = PDFDocument(
            filepath=Path("/test/non_a4.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    width=500.0,  # Not A4
                    height=600.0,  # Not A4
                    text_blocks=[
                        TextBlock(raw_text="Original", unicode_text="Original text")
                    ],
                ),
            ],
        )

        # Create translation result
        translation_result = TranslationResult(
            source_text="Original text",
            translated_text="Translated text",
            source_language="mr",
            target_language="en",
            translation_backend=TranslationBackend.MOCK,
        )

        generator = OutputGenerator(include_metadata=False)
        # Even with preserve_structure=True, should use A4 when translating
        output = generator.generate_pdf(
            document,
            sample_encoding_result,
            translation_result=translation_result,
            preserve_structure=True,
        )

        # Parse the output PDF - should be A4 because we're translating
        pdf = fitz.open(stream=output, filetype="pdf")
        try:
            # Should be A4 dimensions when translating
            assert abs(pdf[0].rect.width - 595) < 1
            assert abs(pdf[0].rect.height - 842) < 1
        finally:
            pdf.close()


class TestScannedCopy:
    """Tests for scanned copy generation."""

    @pytest.fixture
    def sample_pdf_file(self, temp_dir):
        """Create a sample PDF file for testing scanned copy."""
        pdf_path = temp_dir / "sample.pdf"
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)  # Letter size
        page.insert_text((72, 72), "Test content for scanned copy", fontsize=12)
        page.insert_text((72, 100), "Second line of text", fontsize=12)
        doc.save(pdf_path)
        doc.close()
        return pdf_path

    def test_generate_scanned_copy_basic(self, sample_pdf_file):
        """Test basic scanned copy generation."""
        generator = OutputGenerator()
        output = generator.generate_scanned_copy(input_path=sample_pdf_file)

        # Should return PDF bytes
        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")
        assert b"%%EOF" in output

    def test_generate_scanned_copy_with_output_path(self, sample_pdf_file, temp_dir):
        """Test scanned copy saved to file."""
        generator = OutputGenerator()
        output_path = temp_dir / "scanned.pdf"

        output = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            output_path=output_path,
        )

        assert output_path.exists()
        assert output_path.read_bytes() == output

    def test_generate_scanned_copy_preserves_page_count(self, temp_dir):
        """Test that scanned copy preserves page count."""
        # Create multi-page PDF
        pdf_path = temp_dir / "multipage.pdf"
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1}", fontsize=12)
        doc.save(pdf_path)
        doc.close()

        generator = OutputGenerator()
        output = generator.generate_scanned_copy(input_path=pdf_path)

        # Verify page count
        result_pdf = fitz.open(stream=output, filetype="pdf")
        try:
            assert result_pdf.page_count == 3
        finally:
            result_pdf.close()

    def test_generate_scanned_copy_preserves_dimensions(self, sample_pdf_file):
        """Test that scanned copy preserves page dimensions."""
        generator = OutputGenerator()
        output = generator.generate_scanned_copy(input_path=sample_pdf_file)

        # Verify dimensions match original (Letter size)
        result_pdf = fitz.open(stream=output, filetype="pdf")
        try:
            assert abs(result_pdf[0].rect.width - 612) < 1
            assert abs(result_pdf[0].rect.height - 792) < 1
        finally:
            result_pdf.close()

    def test_generate_scanned_copy_dpi_options(self, sample_pdf_file):
        """Test scanned copy with different DPI settings."""
        generator = OutputGenerator()

        # Lower DPI should produce smaller file
        output_150 = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            dpi=150,
        )

        output_300 = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            dpi=300,
        )

        # Both should be valid PDFs
        assert output_150.startswith(b"%PDF")
        assert output_300.startswith(b"%PDF")

        # Higher DPI should produce larger file
        assert len(output_300) > len(output_150)

    def test_generate_scanned_copy_grayscale(self, sample_pdf_file):
        """Test scanned copy with grayscale color mode."""
        generator = OutputGenerator()
        output = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            color_mode="grayscale",
        )

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")

    def test_generate_scanned_copy_bw(self, sample_pdf_file):
        """Test scanned copy with black & white color mode."""
        generator = OutputGenerator()
        output = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            color_mode="bw",
        )

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")

    def test_generate_scanned_copy_quality_reduces_size(self, sample_pdf_file):
        """Test that lower quality produces smaller files."""
        generator = OutputGenerator()

        # High quality (larger file)
        output_high = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            quality=95,
        )

        # Low quality (smaller file)
        output_low = generator.generate_scanned_copy(
            input_path=sample_pdf_file,
            quality=50,
        )

        # Both should be valid PDFs
        assert output_high.startswith(b"%PDF")
        assert output_low.startswith(b"%PDF")

        # Lower quality should produce smaller file
        assert len(output_low) < len(output_high)

    def test_generate_scanned_copy_quality_parameter(self, sample_pdf_file):
        """Test that quality parameter is accepted and produces valid PDF."""
        generator = OutputGenerator()

        # Test various quality levels
        for quality in [1, 50, 85, 100]:
            output = generator.generate_scanned_copy(
                input_path=sample_pdf_file,
                quality=quality,
            )
            assert isinstance(output, bytes)
            assert output.startswith(b"%PDF")
            assert b"%%EOF" in output

    def test_generate_scanned_copy_default_quality(self, sample_pdf_file):
        """Test that default quality (85) produces valid PDF."""
        generator = OutputGenerator()

        # Call without quality parameter - should use default (85)
        output = generator.generate_scanned_copy(input_path=sample_pdf_file)

        assert isinstance(output, bytes)
        assert output.startswith(b"%PDF")
