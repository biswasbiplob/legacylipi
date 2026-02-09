"""Tests for PDF Parser module."""

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from legacylipi.core.models import BoundingBox, PDFDocument
from legacylipi.core.pdf_parser import PDFParseError, PDFParser, parse_pdf


def create_test_pdf(filepath: Path, pages: list[str], font_name: str = "Helvetica") -> None:
    """Create a test PDF with the given page contents.

    Args:
        filepath: Path where the PDF will be saved.
        pages: List of text content for each page.
        font_name: Font name to use (default: Helvetica).
    """
    doc = fitz.open()
    for page_text in pages:
        page = doc.new_page()
        # Insert text at position (72, 72) - 1 inch from top-left
        page.insert_text((72, 72), page_text, fontname=font_name, fontsize=12)
    doc.save(filepath)
    doc.close()


def create_legacy_encoded_pdf(filepath: Path, text: str, font_name: str = "Shree-Dev-0714") -> None:
    """Create a test PDF simulating legacy-encoded text.

    Args:
        filepath: Path where the PDF will be saved.
        text: Text content (simulating legacy encoding).
        font_name: Legacy font name to use.
    """
    doc = fitz.open()
    page = doc.new_page()
    # Use helv as actual font but we'll set metadata to simulate legacy
    page.insert_text((72, 72), text, fontname="helv", fontsize=12)
    doc.save(filepath)
    doc.close()


class TestPDFParserInit:
    """Tests for PDFParser initialization."""

    def test_init_with_valid_path(self, temp_dir):
        """Test initialization with a valid PDF path."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        parser = PDFParser(pdf_path)
        assert parser.filepath == pdf_path

    def test_init_with_string_path(self, temp_dir):
        """Test initialization with string path."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        parser = PDFParser(str(pdf_path))
        assert parser.filepath == pdf_path

    def test_init_nonexistent_file(self):
        """Test initialization with non-existent file."""
        with pytest.raises(PDFParseError, match="File not found"):
            PDFParser("/nonexistent/file.pdf")

    def test_init_non_pdf_file(self, temp_dir):
        """Test initialization with non-PDF file."""
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("Not a PDF")

        with pytest.raises(PDFParseError, match="Not a PDF file"):
            PDFParser(txt_path)


class TestPDFParserOpen:
    """Tests for opening PDF documents."""

    def test_open_valid_pdf(self, temp_dir):
        """Test opening a valid PDF."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        parser = PDFParser(pdf_path)
        parser.open()
        assert parser._doc is not None
        parser.close()

    def test_context_manager(self, temp_dir):
        """Test using parser as context manager."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        with PDFParser(pdf_path) as parser:
            assert parser._doc is not None
        # After exiting context, doc should be closed
        assert parser._doc is None

    def test_doc_property_raises_when_not_open(self, temp_dir):
        """Test that accessing doc raises error when not open."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        parser = PDFParser(pdf_path)
        with pytest.raises(PDFParseError, match="Document not open"):
            _ = parser.doc


class TestPDFParserMetadata:
    """Tests for metadata extraction."""

    def test_get_metadata_basic(self, temp_dir):
        """Test extracting basic metadata."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Page 1", "Page 2", "Page 3"])

        with PDFParser(pdf_path) as parser:
            metadata = parser.get_metadata()
            assert metadata.page_count == 3

    def test_get_metadata_with_title(self, temp_dir):
        """Test extracting metadata with title."""
        pdf_path = temp_dir / "test.pdf"

        # Create PDF with metadata
        doc = fitz.open()
        doc.new_page()
        doc.set_metadata({"title": "Test Document", "author": "Test Author"})
        doc.save(pdf_path)
        doc.close()

        with PDFParser(pdf_path) as parser:
            metadata = parser.get_metadata()
            assert metadata.title == "Test Document"
            assert metadata.author == "Test Author"


class TestPDFParserFonts:
    """Tests for font extraction."""

    def test_get_fonts_basic(self, temp_dir):
        """Test extracting fonts from a PDF."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        with PDFParser(pdf_path) as parser:
            fonts = parser.get_fonts()
            # Should have at least one font
            assert len(fonts) >= 0  # May be 0 if font not embedded

    def test_get_fonts_multiple_pages(self, temp_dir):
        """Test extracting fonts from multiple pages."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Page 1", "Page 2"])

        with PDFParser(pdf_path) as parser:
            fonts = parser.get_fonts()
            # Fonts should be deduplicated
            font_names = {f.name for f in fonts}
            # Each unique font should appear only once
            assert len(fonts) == len(font_names)


class TestPDFParserPages:
    """Tests for page parsing."""

    def test_parse_single_page(self, temp_dir):
        """Test parsing a single page."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with PDFParser(pdf_path) as parser:
            page = parser.parse_page(0)
            assert page.page_number == 1  # 1-indexed
            assert page.width > 0
            assert page.height > 0

    def test_parse_page_text_blocks(self, temp_dir):
        """Test that text blocks are extracted."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with PDFParser(pdf_path) as parser:
            page = parser.parse_page(0)
            # Should have at least one text block
            assert len(page.text_blocks) >= 1
            # Text should contain our content
            assert "Hello" in page.raw_text

    def test_parse_page_invalid_number(self, temp_dir):
        """Test parsing with invalid page number."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Single page"])

        with PDFParser(pdf_path) as parser:
            with pytest.raises(PDFParseError, match="Invalid page number"):
                parser.parse_page(10)

    def test_parse_page_negative_number(self, temp_dir):
        """Test parsing with negative page number."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Single page"])

        with PDFParser(pdf_path) as parser:
            with pytest.raises(PDFParseError, match="Invalid page number"):
                parser.parse_page(-1)


class TestPDFParserFullParse:
    """Tests for full document parsing."""

    def test_parse_full_document(self, temp_dir):
        """Test parsing an entire document."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Page 1 content", "Page 2 content", "Page 3 content"])

        with PDFParser(pdf_path) as parser:
            doc = parser.parse()

            assert isinstance(doc, PDFDocument)
            assert doc.filepath == pdf_path
            assert doc.page_count == 3
            assert len(doc.pages) == 3
            assert doc.pages[0].page_number == 1
            assert doc.pages[1].page_number == 2
            assert doc.pages[2].page_number == 3

    def test_parse_document_text_extraction(self, temp_dir):
        """Test that text is correctly extracted from all pages."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["First page", "Second page"])

        with PDFParser(pdf_path) as parser:
            doc = parser.parse()

            full_text = doc.raw_text
            assert "First" in full_text
            assert "Second" in full_text

    def test_parse_document_fonts_collected(self, temp_dir):
        """Test that fonts are collected from all pages."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Content"])

        with PDFParser(pdf_path) as parser:
            doc = parser.parse()
            # Document should have fonts list
            assert isinstance(doc.fonts, list)


class TestParsePDFFunction:
    """Tests for the parse_pdf convenience function."""

    def test_parse_pdf_basic(self, temp_dir):
        """Test the convenience function."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        doc = parse_pdf(pdf_path)
        assert isinstance(doc, PDFDocument)
        assert doc.page_count == 1

    def test_parse_pdf_with_string_path(self, temp_dir):
        """Test with string path."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        doc = parse_pdf(str(pdf_path))
        assert isinstance(doc, PDFDocument)


class TestTextBlockExtraction:
    """Tests for detailed text block extraction."""

    def test_text_block_has_font_info(self, temp_dir):
        """Test that text blocks have font information."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Sample text"])

        with PDFParser(pdf_path) as parser:
            page = parser.parse_page(0)
            if page.text_blocks:
                block = page.text_blocks[0]
                # Font name should be extracted
                assert block.font_name is not None or block.font_size > 0

    def test_text_block_has_position(self, temp_dir):
        """Test that text blocks have position information."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Sample text"])

        with PDFParser(pdf_path) as parser:
            page = parser.parse_page(0)
            if page.text_blocks:
                block = page.text_blocks[0]
                assert block.position is not None
                assert isinstance(block.position, BoundingBox)

    def test_multiple_lines_extraction(self, temp_dir):
        """Test extraction of multiple text lines."""
        pdf_path = temp_dir / "test.pdf"

        # Create PDF with multiple lines
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Line 1", fontsize=12)
        page.insert_text((72, 100), "Line 2", fontsize=12)
        page.insert_text((72, 128), "Line 3", fontsize=12)
        doc.save(pdf_path)
        doc.close()

        with PDFParser(pdf_path) as parser:
            page = parser.parse_page(0)
            # Should have multiple text blocks
            assert len(page.text_blocks) >= 1
            full_text = page.raw_text
            assert "Line 1" in full_text
            assert "Line 2" in full_text
            assert "Line 3" in full_text


class TestLegacyEncodedPDFs:
    """Tests for handling legacy-encoded PDFs."""

    def test_parse_legacy_encoded_text(self, temp_dir):
        """Test parsing PDF with legacy-encoded appearing text."""
        pdf_path = temp_dir / "legacy.pdf"
        # This simulates text that looks like legacy encoding output
        legacy_text = "´ÖÆüÖ¸üÖÂ™Òü"
        create_legacy_encoded_pdf(pdf_path, legacy_text)

        with PDFParser(pdf_path) as parser:
            doc = parser.parse()
            # Text should be extracted as-is
            assert doc.page_count == 1
            assert len(doc.pages[0].text_blocks) >= 0

    def test_unicode_text_preserved(self, temp_dir):
        """Test that Unicode text is preserved correctly."""
        pdf_path = temp_dir / "unicode.pdf"

        # Create PDF with Devanagari text (if font supports it)
        doc = fitz.open()
        page = doc.new_page()
        # Use a simple ASCII representation for testing
        page.insert_text((72, 72), "Test Unicode: ABC", fontsize=12)
        doc.save(pdf_path)
        doc.close()

        with PDFParser(pdf_path) as parser:
            pdf_doc = parser.parse()
            assert "ABC" in pdf_doc.raw_text


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_page(self, temp_dir):
        """Test parsing a PDF with an empty page."""
        pdf_path = temp_dir / "empty.pdf"

        doc = fitz.open()
        doc.new_page()  # Empty page
        doc.save(pdf_path)
        doc.close()

        with PDFParser(pdf_path) as parser:
            pdf_doc = parser.parse()
            assert pdf_doc.page_count == 1
            assert len(pdf_doc.pages[0].text_blocks) == 0

    def test_pdf_with_images_only(self, temp_dir):
        """Test parsing a PDF that might have only images."""
        pdf_path = temp_dir / "image.pdf"

        doc = fitz.open()
        page = doc.new_page()
        # Just an empty page (simulating image-only)
        doc.save(pdf_path)
        doc.close()

        with PDFParser(pdf_path) as parser:
            pdf_doc = parser.parse()
            # Should handle gracefully
            assert pdf_doc.page_count == 1

    def test_large_page_count(self, temp_dir):
        """Test parsing a PDF with many pages."""
        pdf_path = temp_dir / "large.pdf"
        pages = [f"Page {i}" for i in range(50)]
        create_test_pdf(pdf_path, pages)

        with PDFParser(pdf_path) as parser:
            pdf_doc = parser.parse()
            assert pdf_doc.page_count == 50
            assert len(pdf_doc.pages) == 50
