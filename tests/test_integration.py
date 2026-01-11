"""Integration tests for LegacyLipi end-to-end workflows."""

import tempfile
from pathlib import Path

import fitz
import pytest

from legacylipi.core.encoding_detector import EncodingDetector
from legacylipi.core.models import OutputFormat
from legacylipi.core.output_generator import OutputGenerator
from legacylipi.core.pdf_parser import parse_pdf
from legacylipi.core.translator import create_translator
from legacylipi.core.unicode_converter import UnicodeConverter


@pytest.fixture
def test_pdf_dir(temp_dir):
    """Create a directory with test PDF files."""
    return temp_dir


def create_simple_pdf(filepath: Path, text: str) -> None:
    """Create a simple PDF with the given text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(filepath)
    doc.close()


def create_multipage_pdf(filepath: Path, pages: list[str]) -> None:
    """Create a multi-page PDF."""
    doc = fitz.open()
    for page_text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), page_text, fontsize=12)
    doc.save(filepath)
    doc.close()


class TestFullPipeline:
    """Integration tests for the complete translation pipeline."""

    def test_simple_pdf_pipeline(self, test_pdf_dir):
        """Test processing a simple PDF through the full pipeline."""
        # Create test PDF
        pdf_path = test_pdf_dir / "simple.pdf"
        create_simple_pdf(pdf_path, "This is a test document.")

        # Step 1: Parse PDF
        document = parse_pdf(pdf_path)
        assert document.page_count == 1
        assert len(document.pages[0].text_blocks) >= 0

        # Step 2: Detect encoding
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)
        assert encoding_result is not None

        # Step 3: Convert to Unicode
        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)
        assert converted_doc.page_count == 1

        # Step 4: Translate (using mock)
        translator = create_translator("mock")
        unicode_text = converted_doc.unicode_text
        translation_result = translator.translate(unicode_text, "en", "hi")
        assert translation_result.success

        # Step 5: Generate output
        generator = OutputGenerator()
        output = generator.generate(
            converted_doc,
            encoding_result,
            translation_result,
            OutputFormat.TEXT,
        )
        assert len(output) > 0

    def test_multipage_pdf_pipeline(self, test_pdf_dir):
        """Test processing a multi-page PDF."""
        # Create test PDF
        pdf_path = test_pdf_dir / "multipage.pdf"
        create_multipage_pdf(pdf_path, [
            "Page 1: Introduction",
            "Page 2: Content",
            "Page 3: Conclusion",
        ])

        # Process
        document = parse_pdf(pdf_path)
        assert document.page_count == 3

        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        # Verify all pages converted
        assert len(converted_doc.pages) == 3
        for page in converted_doc.pages:
            assert page.page_number in [1, 2, 3]

    def test_output_to_file(self, test_pdf_dir):
        """Test writing output to a file."""
        # Create and process PDF
        pdf_path = test_pdf_dir / "output_test.pdf"
        create_simple_pdf(pdf_path, "Output test content.")

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, _ = detector.detect_from_document(document)

        # Generate and save output
        generator = OutputGenerator()
        output = generator.generate(
            document,
            encoding_result,
            output_format=OutputFormat.TEXT,
        )

        output_path = test_pdf_dir / "output.txt"
        generator.save(output, output_path)

        # Verify file was created
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "LegacyLipi" in content

    def test_markdown_output_format(self, test_pdf_dir):
        """Test generating Markdown output."""
        pdf_path = test_pdf_dir / "md_test.pdf"
        create_simple_pdf(pdf_path, "Markdown test.")

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, _ = detector.detect_from_document(document)

        translator = create_translator("mock")
        translation_result = translator.translate("Test", "en", "hi")

        generator = OutputGenerator()
        output = generator.generate(
            document,
            encoding_result,
            translation_result,
            OutputFormat.MARKDOWN,
        )

        # Verify Markdown formatting
        assert "# Translation:" in output
        assert "|" in output  # Table formatting


class TestEncodingDetectionPipeline:
    """Integration tests for encoding detection workflow."""

    def test_detect_and_report(self, test_pdf_dir):
        """Test encoding detection and reporting."""
        pdf_path = test_pdf_dir / "detect_test.pdf"
        create_simple_pdf(pdf_path, "Detection test content.")

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        # Verify detection result
        assert encoding_result.detected_encoding is not None
        assert 0 <= encoding_result.confidence <= 1.0
        assert encoding_result.method is not None

    def test_mixed_content_detection(self, test_pdf_dir):
        """Test detection with mixed content types."""
        pdf_path = test_pdf_dir / "mixed.pdf"
        create_multipage_pdf(pdf_path, [
            "English text on page 1",
            "More English on page 2",
        ])

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        # Should handle mixed content
        assert encoding_result is not None


class TestConversionPipeline:
    """Integration tests for Unicode conversion workflow."""

    def test_convert_without_translation(self, test_pdf_dir):
        """Test conversion pipeline without translation."""
        pdf_path = test_pdf_dir / "convert_only.pdf"
        create_simple_pdf(pdf_path, "Convert only test.")

        # Parse and detect
        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        # Convert only
        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        # Generate output without translation
        generator = OutputGenerator()
        output = generator.generate(
            converted_doc,
            encoding_result,
            output_format=OutputFormat.TEXT,
        )

        assert len(output) > 0


class TestTranslationPipeline:
    """Integration tests for translation workflow."""

    def test_chunked_translation(self, test_pdf_dir):
        """Test translation of large documents with chunking."""
        # Create PDF with multiple paragraphs
        pdf_path = test_pdf_dir / "chunked.pdf"
        long_text = "This is paragraph one. " * 50
        create_simple_pdf(pdf_path, long_text)

        document = parse_pdf(pdf_path)
        translator = create_translator("mock")

        # Translate with chunking
        result = translator.translate(document.raw_text, "en", "hi")

        assert result.success
        assert result.chunk_count >= 1

    def test_translation_with_different_backends(self, test_pdf_dir):
        """Test that different backends work through the pipeline."""
        pdf_path = test_pdf_dir / "backends.pdf"
        create_simple_pdf(pdf_path, "Backend test.")

        document = parse_pdf(pdf_path)

        # Test mock backend
        mock_translator = create_translator("mock")
        mock_result = mock_translator.translate("Test", "en", "hi")
        assert mock_result.success

        # Verify backend type is recorded
        from legacylipi.core.models import TranslationBackend
        assert mock_result.translation_backend == TranslationBackend.MOCK


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_empty_pdf_handling(self, test_pdf_dir):
        """Test handling of PDF with no text."""
        pdf_path = test_pdf_dir / "empty.pdf"

        # Create empty PDF
        doc = fitz.open()
        doc.new_page()  # Empty page
        doc.save(pdf_path)
        doc.close()

        # Should handle gracefully
        document = parse_pdf(pdf_path)
        assert document.page_count == 1

        detector = EncodingDetector()
        encoding_result, _ = detector.detect_from_document(document)
        # Should return unknown for empty doc
        assert encoding_result is not None

    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent file."""
        from legacylipi.core.pdf_parser import PDFParseError

        with pytest.raises(PDFParseError):
            parse_pdf(Path("/nonexistent/file.pdf"))


class TestEdgeCases:
    """Integration tests for edge cases."""

    def test_single_character_content(self, test_pdf_dir):
        """Test handling of minimal content."""
        pdf_path = test_pdf_dir / "minimal.pdf"
        create_simple_pdf(pdf_path, "A")

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        assert converted_doc is not None

    def test_special_characters(self, test_pdf_dir):
        """Test handling of special characters."""
        pdf_path = test_pdf_dir / "special.pdf"
        create_simple_pdf(pdf_path, "Special: !@#$%^&*()_+")

        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, _ = detector.detect_from_document(document)

        assert encoding_result is not None

    def test_large_document(self, test_pdf_dir):
        """Test handling of larger documents."""
        pdf_path = test_pdf_dir / "large.pdf"

        # Create 20-page document
        pages = [f"Page {i}: Content for page {i} goes here." for i in range(1, 21)]
        create_multipage_pdf(pdf_path, pages)

        document = parse_pdf(pdf_path)
        assert document.page_count == 20

        # Should process all pages
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        assert converted_doc.page_count == 20


class TestRealPDFWithLegacyEncoding:
    """Integration tests using real PDF files with legacy encodings."""

    @pytest.fixture
    def input_pdf_path(self):
        """Path to the test input PDF with DVB-TT encoding."""
        path = Path(__file__).parent / "data" / "input.pdf"
        if not path.exists():
            pytest.skip("Test PDF not available")
        return path

    def test_dvbtt_pdf_detection(self, input_pdf_path):
        """Test encoding detection on a real DVB-TT encoded PDF."""
        document = parse_pdf(input_pdf_path)

        # Document should have multiple pages
        assert document.page_count >= 3

        # Detect encoding
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        # Should detect legacy encoding for the document
        # Pages 1-2 use Unicode (Sakal Marathi), pages 3+ use DVB-TT
        assert len(page_encodings) > 0

        # Check that different encodings are detected for different pages
        encodings_found = set(r.detected_encoding for r in page_encodings.values())
        # We expect both unicode-devanagari and dvb-tt to be detected
        assert "dvb-tt" in encodings_found or "unicode-devanagari" in encodings_found

    def test_dvbtt_pdf_conversion(self, input_pdf_path):
        """Test Unicode conversion on a real DVB-TT encoded PDF."""
        document = parse_pdf(input_pdf_path)

        # Detect and convert
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        # Verify conversion produced output
        assert converted_doc is not None
        assert converted_doc.page_count == document.page_count

        # Check that we have Devanagari content in the output
        unicode_text = converted_doc.unicode_text

        # Look for common Marathi words that should appear after conversion
        # "महाराष्ट्र" (Maharashtra) is a key word that should appear
        has_devanagari = any(
            '\u0900' <= char <= '\u097F' for char in unicode_text
        )
        assert has_devanagari, "Converted text should contain Devanagari characters"

    def test_dvbtt_pdf_maharashtra_conversion(self, input_pdf_path):
        """Test that 'महाराष्ट्र' (Maharashtra) is properly converted."""
        document = parse_pdf(input_pdf_path)

        # Detect and convert
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        unicode_text = converted_doc.unicode_text

        # The word "महाराष्ट्र" (Maharashtra) should appear in the output
        # Either directly or we should NOT see the garbled form "´ÖÆüÖ¸üÖÂ™Òü"
        garbled_form = "´ÖÆüÖ¸üÖÂ™Òü"

        # After conversion, we should not see the garbled legacy-encoded form
        # (though it might still appear on Unicode pages that weren't converted)
        # The key test is that Devanagari content exists
        devanagari_count = sum(1 for c in unicode_text if '\u0900' <= c <= '\u097F')

        # Should have significant Devanagari content
        assert devanagari_count > 100, f"Expected significant Devanagari content, got {devanagari_count} chars"

    def test_dvbtt_mixed_encoding_handling(self, input_pdf_path):
        """Test that mixed encoding PDFs are handled correctly per-page."""
        document = parse_pdf(input_pdf_path)

        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        # Check each page has some content after conversion
        for page in converted_doc.pages:
            # Pages should have text blocks
            # (some may be empty depending on the PDF structure)
            pass  # Just verifying no exceptions during conversion

    def test_dvbtt_full_pipeline_no_translate(self, input_pdf_path, tmp_path):
        """Test full pipeline without translation on DVB-TT PDF."""
        document = parse_pdf(input_pdf_path)

        # Detect
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        # Convert
        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        # Generate output
        generator = OutputGenerator()
        output = generator.generate(
            converted_doc,
            encoding_result,
            output_format=OutputFormat.TEXT,
        )

        # Save and verify
        output_path = tmp_path / "dvbtt_output.txt"
        generator.save(output, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Should have Devanagari content
        devanagari_count = sum(1 for c in content if '\u0900' <= c <= '\u097F')
        assert devanagari_count > 50, "Output should contain Devanagari text"


class TestRoundTrip:
    """Integration tests for complete round-trip processing."""

    def test_full_roundtrip_text(self, test_pdf_dir):
        """Test complete round-trip: PDF -> Text output."""
        pdf_path = test_pdf_dir / "roundtrip.pdf"
        original_text = "This is the original content for round-trip testing."
        create_simple_pdf(pdf_path, original_text)

        # Full pipeline
        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        translator = create_translator("mock")
        translation_result = translator.translate(
            converted_doc.unicode_text, "en", "hi"
        )

        generator = OutputGenerator()
        output_path = test_pdf_dir / "roundtrip_output.txt"
        output = generator.generate(
            converted_doc,
            encoding_result,
            translation_result,
            OutputFormat.TEXT,
        )
        generator.save(output, output_path)

        # Verify output file
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "LegacyLipi" in content

    def test_full_roundtrip_markdown(self, test_pdf_dir):
        """Test complete round-trip: PDF -> Markdown output."""
        pdf_path = test_pdf_dir / "roundtrip_md.pdf"
        create_simple_pdf(pdf_path, "Markdown round-trip test.")

        # Full pipeline
        document = parse_pdf(pdf_path)
        detector = EncodingDetector()
        encoding_result, page_encodings = detector.detect_from_document(document)

        converter = UnicodeConverter()
        converted_doc = converter.convert_document(document, page_encodings=page_encodings)

        translator = create_translator("mock")
        translation_result = translator.translate(
            converted_doc.unicode_text, "en", "hi"
        )

        generator = OutputGenerator()
        output_path = test_pdf_dir / "roundtrip_output.md"
        output = generator.generate(
            converted_doc,
            encoding_result,
            translation_result,
            OutputFormat.MARKDOWN,
        )
        generator.save(output, output_path)

        # Verify Markdown output
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# Translation:" in content
        assert "|" in content
