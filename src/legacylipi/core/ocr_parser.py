"""OCR-based PDF Parser module.

This module provides OCR-based text extraction from PDF documents.
It converts PDF pages to images and uses Tesseract OCR to extract
text, particularly useful for legacy Marathi documents.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from legacylipi.core.models import (
    BoundingBox,
    DocumentMetadata,
    PDFDocument,
    PDFPage,
    TextBlock,
)

# Check if pytesseract is available
try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class OCRError(Exception):
    """Exception raised when OCR processing fails."""
    pass


class TesseractNotFoundError(OCRError):
    """Exception raised when Tesseract is not installed."""
    pass


class LanguageNotAvailableError(OCRError):
    """Exception raised when requested OCR language is not available."""
    pass


def check_tesseract_available() -> tuple[bool, str]:
    """Check if Tesseract OCR is available.

    Returns:
        Tuple of (is_available, message).
    """
    tesseract_path = shutil.which("tesseract")
    if tesseract_path is None:
        return False, "Tesseract OCR not found. Install with: sudo apt-get install tesseract-ocr"

    try:
        result = subprocess.run(
            [tesseract_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
        return True, f"Tesseract available: {version_line}"
    except Exception as e:
        return False, f"Tesseract check failed: {e}"


def get_available_languages() -> list[str]:
    """Get list of available OCR languages.

    Returns:
        List of language codes available for OCR.
    """
    tesseract_path = shutil.which("tesseract")
    if tesseract_path is None:
        return []

    try:
        result = subprocess.run(
            [tesseract_path, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Parse output - first line is header, rest are language codes
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            return [lang.strip() for lang in lines[1:] if lang.strip()]
        return []
    except Exception:
        return []


def check_language_available(lang: str) -> bool:
    """Check if a specific language is available for OCR.

    Args:
        lang: Language code (e.g., 'mar' for Marathi, 'eng' for English).

    Returns:
        True if language is available.
    """
    available = get_available_languages()
    return lang in available


class OCRParser:
    """OCR-based parser for extracting text from PDF documents."""

    # Default DPI for rendering PDF pages to images
    DEFAULT_DPI = 300

    # Language codes for common Indian languages
    LANGUAGE_CODES = {
        'marathi': 'mar',
        'mr': 'mar',
        'hindi': 'hin',
        'hi': 'hin',
        'english': 'eng',
        'en': 'eng',
        'devanagari': 'mar+hin',  # Combined for scripts
    }

    def __init__(
        self,
        filepath: Path | str,
        lang: str = "mar",
        dpi: int = DEFAULT_DPI,
        psm: int = 3,  # Page segmentation mode: 3 = fully automatic
    ):
        """Initialize the OCR parser.

        Args:
            filepath: Path to the PDF file.
            lang: OCR language code (e.g., 'mar' for Marathi).
            dpi: DPI for rendering PDF pages to images.
            psm: Tesseract page segmentation mode.

        Raises:
            OCRError: If file doesn't exist or isn't a PDF.
            TesseractNotFoundError: If Tesseract isn't installed.
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise OCRError(f"File not found: {self.filepath}")
        if not self.filepath.suffix.lower() == ".pdf":
            raise OCRError(f"Not a PDF file: {self.filepath}")

        # Normalize language code
        self.lang = self.LANGUAGE_CODES.get(lang.lower(), lang)
        self.dpi = dpi
        self.psm = psm

        # Check dependencies
        if not PYTESSERACT_AVAILABLE:
            raise OCRError(
                "pytesseract not installed. Install with: pip install pytesseract pillow"
            )

        available, msg = check_tesseract_available()
        if not available:
            raise TesseractNotFoundError(msg)

        self._doc: Optional[fitz.Document] = None

    def __enter__(self) -> "OCRParser":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def open(self, password: Optional[str] = None) -> None:
        """Open the PDF document.

        Args:
            password: Password for encrypted PDFs.
        """
        try:
            self._doc = fitz.open(self.filepath)
            if self._doc.is_encrypted:
                if password:
                    if not self._doc.authenticate(password):
                        raise OCRError("Invalid password for encrypted PDF")
                else:
                    raise OCRError("PDF is encrypted. Password required.")
        except fitz.FileDataError as e:
            raise OCRError(f"Invalid PDF file: {e}")

    def close(self) -> None:
        """Close the PDF document."""
        if self._doc:
            self._doc.close()
            self._doc = None

    @property
    def doc(self) -> fitz.Document:
        """Get the underlying fitz document."""
        if self._doc is None:
            raise OCRError("Document not open. Call open() first.")
        return self._doc

    def get_metadata(self) -> DocumentMetadata:
        """Extract document metadata.

        Returns:
            DocumentMetadata object.
        """
        metadata = self.doc.metadata or {}
        return DocumentMetadata(
            title=metadata.get("title") or None,
            author=metadata.get("author") or None,
            subject=metadata.get("subject") or None,
            creator=metadata.get("creator") or None,
            producer=metadata.get("producer") or None,
            creation_date=metadata.get("creationDate") or None,
            modification_date=metadata.get("modDate") or None,
            page_count=len(self.doc),
        )

    def render_page_to_image(self, page_number: int) -> "Image.Image":
        """Render a PDF page to a PIL Image.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            PIL Image of the page.
        """
        if page_number < 0 or page_number >= len(self.doc):
            raise OCRError(
                f"Invalid page number: {page_number}. Document has {len(self.doc)} pages."
            )

        page = self.doc[page_number]

        # Calculate zoom factor for desired DPI (PDF default is 72 DPI)
        zoom = self.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to PIL Image
        img = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

        return img

    def ocr_page(self, page_number: int) -> tuple[str, list[dict]]:
        """Perform OCR on a single page.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            Tuple of (full_text, word_data) where word_data contains
            bounding box information for each word.
        """
        # Render page to image
        img = self.render_page_to_image(page_number)

        # Configure Tesseract
        config = f"--psm {self.psm}"

        # Get full text
        full_text = pytesseract.image_to_string(
            img,
            lang=self.lang,
            config=config
        )

        # Get detailed word/line data with bounding boxes
        try:
            ocr_data = pytesseract.image_to_data(
                img,
                lang=self.lang,
                config=config,
                output_type=pytesseract.Output.DICT
            )

            word_data = []
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if text:
                    word_data.append({
                        'text': text,
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'conf': ocr_data['conf'][i],
                        'line_num': ocr_data['line_num'][i],
                        'block_num': ocr_data['block_num'][i],
                    })
        except Exception:
            # Fall back to simple text extraction without bounding boxes
            word_data = []

        return full_text, word_data

    def parse_page(self, page_number: int) -> PDFPage:
        """Parse a single page using OCR.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            PDFPage object with extracted text blocks.
        """
        page = self.doc[page_number]
        rect = page.rect

        pdf_page = PDFPage(
            page_number=page_number + 1,  # 1-indexed for user-facing
            width=rect.width,
            height=rect.height,
        )

        # Perform OCR
        full_text, word_data = self.ocr_page(page_number)

        if word_data:
            # Group words by line/block for better structure
            blocks = self._group_words_into_blocks(word_data, rect)
            pdf_page.text_blocks = blocks
        elif full_text.strip():
            # Fall back to single text block
            pdf_page.text_blocks = [
                TextBlock(
                    raw_text=full_text.strip(),
                    unicode_text=full_text.strip(),  # OCR output is already Unicode
                    confidence=0.8,  # Default confidence for full-page OCR
                )
            ]

        return pdf_page

    def _group_words_into_blocks(
        self,
        word_data: list[dict],
        page_rect: fitz.Rect
    ) -> list[TextBlock]:
        """Group OCR words into text blocks by line/block.

        Args:
            word_data: List of word dictionaries from OCR.
            page_rect: Page rectangle for coordinate scaling.

        Returns:
            List of TextBlock objects.
        """
        # Scale factor from image coordinates to PDF coordinates
        scale_x = page_rect.width / (self.dpi / 72.0 * page_rect.width)
        scale_y = page_rect.height / (self.dpi / 72.0 * page_rect.height)

        # Group words by block and line
        blocks_dict: dict[tuple[int, int], list[dict]] = {}
        for word in word_data:
            key = (word['block_num'], word['line_num'])
            if key not in blocks_dict:
                blocks_dict[key] = []
            blocks_dict[key].append(word)

        # Convert to TextBlock objects
        text_blocks = []
        for (block_num, line_num), words in sorted(blocks_dict.items()):
            line_text = " ".join(w['text'] for w in words)

            # Calculate bounding box
            min_left = min(w['left'] for w in words)
            min_top = min(w['top'] for w in words)
            max_right = max(w['left'] + w['width'] for w in words)
            max_bottom = max(w['top'] + w['height'] for w in words)

            # Average confidence
            confidences = [w['conf'] for w in words if w['conf'] >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            text_blocks.append(
                TextBlock(
                    raw_text=line_text,
                    unicode_text=line_text,  # OCR output is already Unicode
                    position=BoundingBox(
                        x0=min_left * scale_x,
                        y0=min_top * scale_y,
                        x1=max_right * scale_x,
                        y1=max_bottom * scale_y,
                    ),
                    confidence=avg_conf / 100.0,  # Tesseract returns 0-100
                )
            )

        return text_blocks

    def parse(self, password: Optional[str] = None) -> PDFDocument:
        """Parse the entire PDF using OCR.

        Args:
            password: Password for encrypted PDFs.

        Returns:
            PDFDocument with OCR-extracted text.
        """
        need_close = False
        if self._doc is None:
            self.open(password)
            need_close = True

        try:
            metadata = self.get_metadata()

            pages = []
            for i in range(len(self.doc)):
                page = self.parse_page(i)
                pages.append(page)

            return PDFDocument(
                filepath=self.filepath,
                pages=pages,
                metadata=metadata,
                fonts=[],  # OCR doesn't extract font information
            )
        finally:
            if need_close:
                self.close()


def parse_pdf_with_ocr(
    filepath: Path | str,
    lang: str = "mar",
    dpi: int = 300,
    password: Optional[str] = None
) -> PDFDocument:
    """Convenience function to parse a PDF using OCR.

    Args:
        filepath: Path to the PDF file.
        lang: OCR language code.
        dpi: DPI for rendering.
        password: Password for encrypted PDFs.

    Returns:
        PDFDocument with OCR-extracted text.
    """
    with OCRParser(filepath, lang=lang, dpi=dpi) as parser:
        return parser.parse(password)
