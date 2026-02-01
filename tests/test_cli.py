"""Tests for CLI module."""

import tempfile
from pathlib import Path

import fitz
import pytest
from click.testing import CliRunner

from legacylipi import __version__
from legacylipi.cli import main


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF for testing."""
    pdf_path = temp_dir / "test.pdf"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test document content", fontsize=12)
    page.insert_text((72, 100), "More text here", fontsize=12)
    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def legacy_pdf(temp_dir):
    """Create a PDF simulating legacy-encoded text."""
    pdf_path = temp_dir / "legacy.pdf"

    doc = fitz.open()
    page = doc.new_page()
    # Use text that might look like legacy encoding output
    page.insert_text((72, 72), "Test legacy content", fontsize=12)
    doc.save(pdf_path)
    doc.close()

    return pdf_path


class TestMainCommand:
    """Tests for the main command group."""

    def test_main_help(self, runner):
        """Test main command help."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "LegacyLipi" in result.output
        assert "translate" in result.output
        assert "detect" in result.output

    def test_version(self, runner):
        """Test version option."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output


class TestDetectCommand:
    """Tests for the detect command."""

    def test_detect_basic(self, runner, sample_pdf):
        """Test basic encoding detection."""
        result = runner.invoke(main, ["detect", str(sample_pdf)])

        assert result.exit_code == 0
        assert "Detected Encoding" in result.output

    def test_detect_verbose(self, runner, sample_pdf):
        """Test verbose detection output."""
        result = runner.invoke(main, ["detect", str(sample_pdf), "--verbose"])

        assert result.exit_code == 0
        # Verbose output should include page-by-page analysis
        assert "Page" in result.output or "Encoding" in result.output

    def test_detect_nonexistent_file(self, runner):
        """Test detection with nonexistent file."""
        result = runner.invoke(main, ["detect", "/nonexistent/file.pdf"])

        assert result.exit_code != 0


class TestConvertCommand:
    """Tests for the convert command."""

    def test_convert_basic(self, runner, sample_pdf, temp_dir):
        """Test basic Unicode conversion."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "convert",
            str(sample_pdf),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        assert "Unicode output saved" in result.output

    def test_convert_with_encoding(self, runner, sample_pdf, temp_dir):
        """Test conversion with forced encoding."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "convert",
            str(sample_pdf),
            "-o", str(output_path),
            "--encoding", "shree-lipi",
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_convert_default_output(self, runner, sample_pdf):
        """Test conversion with default output path."""
        result = runner.invoke(main, ["convert", str(sample_pdf)])

        assert result.exit_code == 0
        # Should create .unicode.txt file
        expected_output = sample_pdf.with_suffix(".unicode.txt")
        assert expected_output.exists()

        # Cleanup
        expected_output.unlink()


class TestTranslateCommand:
    """Tests for the translate command."""

    def test_translate_basic(self, runner, sample_pdf, temp_dir):
        """Test basic translation with mock backend."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_translate_quiet(self, runner, sample_pdf, temp_dir):
        """Test quiet translation."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--translator", "mock",
            "--quiet",
        ])

        assert result.exit_code == 0
        # Quiet mode should have minimal output
        assert f"LegacyLipi v{__version__}" not in result.output

    def test_translate_markdown_format(self, runner, sample_pdf, temp_dir):
        """Test translation with Markdown output."""
        output_path = temp_dir / "output.md"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "markdown",
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        assert output_path.exists()

        content = output_path.read_text()
        assert "#" in content  # Markdown header

    def test_translate_no_translate_flag(self, runner, sample_pdf, temp_dir):
        """Test translation with --no-translate flag."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--no-translate",
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        # Should not mention translation
        assert "Translating" not in result.output

    def test_translate_with_encoding(self, runner, sample_pdf, temp_dir):
        """Test translation with forced encoding."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--encoding", "shree-lipi",
            "--translator", "mock",
        ])

        assert result.exit_code == 0

    def test_translate_nonexistent_file(self, runner):
        """Test translation with nonexistent file."""
        result = runner.invoke(main, [
            "translate",
            "/nonexistent/file.pdf",
        ])

        assert result.exit_code != 0


class TestEncodingsCommand:
    """Tests for the encodings command."""

    def test_list_encodings(self, runner):
        """Test listing supported encodings."""
        result = runner.invoke(main, ["encodings"])

        assert result.exit_code == 0
        assert "Supported Encodings" in result.output
        assert "shree-lipi" in result.output
        assert "kruti-dev" in result.output

    def test_search_encodings(self, runner):
        """Test searching encodings."""
        result = runner.invoke(main, ["encodings", "--search", "shree"])

        assert result.exit_code == 0
        assert "shree-lipi" in result.output


class TestOutputFormats:
    """Tests for different output format options."""

    def test_text_format_option(self, runner, sample_pdf, temp_dir):
        """Test explicit text format option."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "text",
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        content = output_path.read_text()
        assert "LegacyLipi Translation Output" in content

    def test_md_format_alias(self, runner, sample_pdf, temp_dir):
        """Test 'md' as alias for markdown format."""
        output_path = temp_dir / "output.md"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "md",
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        content = output_path.read_text()
        assert "# Translation:" in content

    def test_pdf_format_option(self, runner, sample_pdf, temp_dir):
        """Test PDF format option."""
        output_path = temp_dir / "output.pdf"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "pdf",
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_bytes()
        assert content.startswith(b"%PDF")

    def test_pdf_default_extension(self, runner, sample_pdf, temp_dir):
        """Test that PDF format uses .pdf extension by default."""
        # Don't specify output path - let it use default
        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "--format", "pdf",
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        # Check that it created a .pdf file with the same base name
        expected_output = sample_pdf.with_suffix(".pdf")
        assert expected_output.exists()
        content = expected_output.read_bytes()
        assert content.startswith(b"%PDF")


class TestTranslatorOptions:
    """Tests for translator backend options."""

    def test_mock_translator(self, runner, sample_pdf, temp_dir):
        """Test mock translator backend."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "-o", str(output_path),
            "--translator", "mock",
        ])

        assert result.exit_code == 0
        assert "mock" in result.output.lower() or output_path.exists()

    def test_invalid_translator(self, runner, sample_pdf, temp_dir):
        """Test invalid translator option is handled by Click."""
        result = runner.invoke(main, [
            "translate",
            str(sample_pdf),
            "--translator", "invalid",
        ])

        # Click should reject invalid choice
        assert result.exit_code != 0


class TestExtractCommand:
    """Tests for the extract command."""

    def test_extract_help(self, runner):
        """Test extract command help."""
        result = runner.invoke(main, ["extract", "--help"])

        assert result.exit_code == 0
        assert "Extract text from PDF" in result.output
        assert "--use-ocr" in result.output
        assert "--ocr-lang" in result.output
        assert "--format" in result.output

    def test_extract_basic(self, runner, sample_pdf, temp_dir):
        """Test basic text extraction (font-based)."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        assert "Output saved to" in result.output

    def test_extract_quiet(self, runner, sample_pdf, temp_dir):
        """Test quiet extraction."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
            "--quiet",
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        # Quiet mode should have minimal output
        assert f"LegacyLipi v{__version__}" not in result.output

    def test_extract_default_output(self, runner, sample_pdf):
        """Test extraction with default output path."""
        result = runner.invoke(main, ["extract", str(sample_pdf)])

        assert result.exit_code == 0
        # Should create .extracted.txt file
        expected_output = sample_pdf.with_suffix(".extracted.txt")
        assert expected_output.exists()

        # Cleanup
        expected_output.unlink()

    def test_extract_markdown_format(self, runner, sample_pdf, temp_dir):
        """Test extraction with Markdown output."""
        output_path = temp_dir / "output.md"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "markdown",
        ])

        assert result.exit_code == 0
        assert output_path.exists()

        content = output_path.read_text()
        assert "#" in content  # Markdown header

    def test_extract_pdf_format(self, runner, sample_pdf, temp_dir):
        """Test extraction with PDF output."""
        output_path = temp_dir / "output.pdf"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
            "--format", "pdf",
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_bytes()
        assert content.startswith(b"%PDF")

    def test_extract_with_encoding(self, runner, sample_pdf, temp_dir):
        """Test extraction with forced encoding."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
            "--encoding", "shree-lipi",
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_extract_nonexistent_file(self, runner):
        """Test extraction with nonexistent file."""
        result = runner.invoke(main, [
            "extract",
            "/nonexistent/file.pdf",
        ])

        assert result.exit_code != 0

    def test_extract_summary_shows_method(self, runner, sample_pdf, temp_dir):
        """Test that summary shows extraction method."""
        output_path = temp_dir / "output.txt"

        result = runner.invoke(main, [
            "extract",
            str(sample_pdf),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert "Font-based" in result.output


class TestErrorHandling:
    """Tests for error handling in CLI."""

    def test_invalid_pdf_file(self, runner, temp_dir):
        """Test handling of invalid PDF file."""
        # Create a text file pretending to be PDF
        fake_pdf = temp_dir / "fake.pdf"
        fake_pdf.write_text("Not a PDF")

        result = runner.invoke(main, ["detect", str(fake_pdf)])

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_permission_denied(self, runner):
        """Test handling of permission denied errors."""
        # This test may not work on all systems
        # Just verify the command doesn't crash unexpectedly
        result = runner.invoke(main, ["detect", "/root/test.pdf"])

        # Should exit with error
        assert result.exit_code != 0
