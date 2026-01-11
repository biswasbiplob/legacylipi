"""Tests for OCR Parser module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
import pytest

from legacylipi.core.ocr_parser import (
    PYTESSERACT_AVAILABLE,
    OCRError,
    OCRParser,
    TesseractNotFoundError,
    check_language_available,
    check_tesseract_available,
    get_available_languages,
    parse_pdf_with_ocr,
)


def create_test_pdf(filepath: Path, pages: list[str]) -> None:
    """Create a test PDF with the given page contents."""
    doc = fitz.open()
    for page_text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), page_text, fontsize=12)
    doc.save(filepath)
    doc.close()


def create_pdf_with_unicode_text(filepath: Path, text: str) -> None:
    """Create a test PDF with Unicode text (using TextWriter for proper support)."""
    doc = fitz.open()
    page = doc.new_page()
    # Use TextWriter for better Unicode support
    tw = fitz.TextWriter(page.rect)
    font = fitz.Font("helv")
    tw.append((72, 72), text, font=font, fontsize=12)
    tw.write_text(page)
    doc.save(filepath)
    doc.close()


class TestTesseractAvailability:
    """Tests for Tesseract availability checking."""

    def test_check_tesseract_available_returns_tuple(self):
        """Test that check_tesseract_available returns a tuple."""
        available, msg = check_tesseract_available()
        assert isinstance(available, bool)
        assert isinstance(msg, str)

    def test_get_available_languages_returns_list(self):
        """Test that get_available_languages returns a list."""
        langs = get_available_languages()
        assert isinstance(langs, list)

    @patch("shutil.which")
    def test_check_tesseract_not_installed(self, mock_which):
        """Test when Tesseract is not installed."""
        mock_which.return_value = None
        available, msg = check_tesseract_available()
        assert not available
        assert "not found" in msg.lower()

    @patch("shutil.which")
    def test_get_languages_when_tesseract_not_installed(self, mock_which):
        """Test language listing when Tesseract is not installed."""
        mock_which.return_value = None
        langs = get_available_languages()
        assert langs == []

    def test_check_language_available_returns_bool(self):
        """Test that check_language_available returns a boolean."""
        result = check_language_available("eng")
        assert isinstance(result, bool)


class TestOCRParserInit:
    """Tests for OCRParser initialization."""

    def test_init_nonexistent_file(self):
        """Test initialization with non-existent file."""
        with pytest.raises(OCRError, match="File not found"):
            OCRParser("/nonexistent/file.pdf")

    def test_init_non_pdf_file(self, temp_dir):
        """Test initialization with non-PDF file."""
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("Not a PDF")

        with pytest.raises(OCRError, match="Not a PDF file"):
            OCRParser(txt_path)

    @patch("legacylipi.core.ocr_parser.check_tesseract_available")
    def test_init_tesseract_not_available(self, mock_check, temp_dir):
        """Test initialization when Tesseract is not available."""
        mock_check.return_value = (False, "Tesseract not found")

        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        with pytest.raises(TesseractNotFoundError):
            OCRParser(pdf_path)

    def test_language_code_normalization(self, temp_dir):
        """Test that language codes are normalized correctly."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        # Test normalization mapping
        with patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK")):
            parser = OCRParser(pdf_path, lang="marathi")
            assert parser.lang == "mar"

            parser = OCRParser(pdf_path, lang="mr")
            assert parser.lang == "mar"

            parser = OCRParser(pdf_path, lang="hindi")
            assert parser.lang == "hin"

            parser = OCRParser(pdf_path, lang="hi")
            assert parser.lang == "hin"


class TestOCRParserMocked:
    """Tests for OCRParser with mocked Tesseract."""

    @pytest.fixture
    def mock_tesseract_available(self):
        """Mock Tesseract as available."""
        with patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK")):
            yield

    @pytest.fixture
    def test_pdf(self, temp_dir):
        """Create a test PDF."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])
        return pdf_path

    def test_context_manager(self, test_pdf, mock_tesseract_available):
        """Test using parser as context manager."""
        with OCRParser(test_pdf) as parser:
            assert parser._doc is not None
        assert parser._doc is None

    def test_open_and_close(self, test_pdf, mock_tesseract_available):
        """Test opening and closing document."""
        parser = OCRParser(test_pdf)
        parser.open()
        assert parser._doc is not None
        parser.close()
        assert parser._doc is None

    def test_doc_property_raises_when_not_open(self, test_pdf, mock_tesseract_available):
        """Test doc property raises when document not open."""
        parser = OCRParser(test_pdf)
        with pytest.raises(OCRError, match="Document not open"):
            _ = parser.doc

    def test_get_metadata(self, test_pdf, mock_tesseract_available):
        """Test metadata extraction."""
        with OCRParser(test_pdf) as parser:
            metadata = parser.get_metadata()
            assert metadata.page_count == 1


# Integration tests that require Tesseract to be installed
@pytest.mark.skipif(
    not check_tesseract_available()[0],
    reason="Tesseract OCR not installed"
)
class TestOCRParserIntegration:
    """Integration tests for OCRParser (requires Tesseract)."""

    def test_render_page_to_image(self, temp_dir):
        """Test rendering PDF page to image."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with OCRParser(pdf_path, lang="eng") as parser:
            img = parser.render_page_to_image(0)
            assert img is not None
            assert img.width > 0
            assert img.height > 0

    def test_render_page_invalid_number(self, temp_dir):
        """Test rendering with invalid page number."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Single page"])

        with OCRParser(pdf_path, lang="eng") as parser:
            with pytest.raises(OCRError, match="Invalid page number"):
                parser.render_page_to_image(10)

    @pytest.mark.skipif(
        not check_language_available("eng"),
        reason="English language pack not installed"
    )
    def test_ocr_page_basic(self, temp_dir):
        """Test basic OCR on a page."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with OCRParser(pdf_path, lang="eng") as parser:
            text, word_data = parser.ocr_page(0)
            # OCR should extract some text (may not be exact due to font rendering)
            assert isinstance(text, str)
            assert isinstance(word_data, list)

    @pytest.mark.skipif(
        not check_language_available("eng"),
        reason="English language pack not installed"
    )
    def test_parse_page(self, temp_dir):
        """Test parsing a single page with OCR."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with OCRParser(pdf_path, lang="eng") as parser:
            page = parser.parse_page(0)
            assert page.page_number == 1
            assert page.width > 0
            assert page.height > 0

    @pytest.mark.skipif(
        not check_language_available("eng"),
        reason="English language pack not installed"
    )
    def test_parse_full_document(self, temp_dir):
        """Test parsing full document with OCR."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Page One", "Page Two"])

        with OCRParser(pdf_path, lang="eng") as parser:
            doc = parser.parse()
            assert doc.page_count == 2
            assert len(doc.pages) == 2

    @pytest.mark.skipif(
        not check_language_available("eng"),
        reason="English language pack not installed"
    )
    def test_parse_pdf_with_ocr_convenience_function(self, temp_dir):
        """Test the convenience function."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test content"])

        doc = parse_pdf_with_ocr(pdf_path, lang="eng")
        assert doc.page_count == 1

    @pytest.mark.skipif(
        not check_language_available("eng"),
        reason="English language pack not installed"
    )
    def test_ocr_output_is_unicode(self, temp_dir):
        """Test that OCR output is already Unicode."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Hello World"])

        with OCRParser(pdf_path, lang="eng") as parser:
            page = parser.parse_page(0)
            # Text blocks from OCR should have unicode_text set
            for block in page.text_blocks:
                # unicode_text should be set (same as raw_text for OCR)
                if block.raw_text:
                    assert block.unicode_text is not None


@pytest.mark.skipif(
    not check_tesseract_available()[0] or not check_language_available("mar"),
    reason="Tesseract OCR or Marathi language not installed"
)
class TestOCRParserMarathi:
    """Integration tests for Marathi OCR."""

    def test_marathi_ocr_parse(self, temp_dir):
        """Test OCR parsing with Marathi language."""
        pdf_path = temp_dir / "marathi.pdf"
        # Create a simple PDF (text may not render perfectly without Devanagari font)
        create_test_pdf(pdf_path, ["Test Marathi"])

        # Just verify it doesn't crash with Marathi language setting
        with OCRParser(pdf_path, lang="mar") as parser:
            doc = parser.parse()
            assert doc.page_count == 1


class TestDPISettings:
    """Tests for DPI configuration."""

    @patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK"))
    def test_default_dpi(self, mock_check, temp_dir):
        """Test default DPI setting."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        parser = OCRParser(pdf_path)
        assert parser.dpi == 300  # Default DPI

    @patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK"))
    def test_custom_dpi(self, mock_check, temp_dir):
        """Test custom DPI setting."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        parser = OCRParser(pdf_path, dpi=150)
        assert parser.dpi == 150

        parser = OCRParser(pdf_path, dpi=600)
        assert parser.dpi == 600


class TestPageSegmentationMode:
    """Tests for page segmentation mode configuration."""

    @patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK"))
    def test_default_psm(self, mock_check, temp_dir):
        """Test default PSM setting."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        parser = OCRParser(pdf_path)
        assert parser.psm == 3  # Default: fully automatic

    @patch("legacylipi.core.ocr_parser.check_tesseract_available", return_value=(True, "OK"))
    def test_custom_psm(self, mock_check, temp_dir):
        """Test custom PSM setting."""
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pdf_path, ["Test"])

        parser = OCRParser(pdf_path, psm=6)  # Uniform block of text
        assert parser.psm == 6
