"""OCR-based PDF Parser module.

This module provides OCR-based text extraction from PDF documents.
It supports multiple OCR backends:
- Tesseract OCR (local, free, requires installation)
- Google Cloud Vision API (cloud, paid, best accuracy for Indian languages)
- EasyOCR (local, free, GPU-accelerated with PyTorch)

Particularly useful for legacy Marathi and other Indian language documents.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from legacylipi.core.models import (
    BoundingBox,
    DocumentMetadata,
    PDFDocument,
    PDFPage,
    TextBlock,
)

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

# Check if pytesseract is available
try:
    import pytesseract
    from PIL import Image

    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# Check if Google Cloud Vision is available
try:
    from google.cloud import vision

    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

# Check if EasyOCR is available
try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


def detect_gpu_backend() -> tuple[bool, str]:
    """Detect available GPU backend for EasyOCR/PyTorch.

    Checks for CUDA (NVIDIA) and MPS (Apple Silicon) backends.

    Returns:
        Tuple of (gpu_available, backend_name) where backend_name is
        "cuda", "mps", or "cpu".
    """
    try:
        import torch

        if torch.cuda.is_available():
            return True, "cuda"
        # Check for Apple Silicon MPS (Metal Performance Shaders)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return True, "mps"
    except ImportError:
        logger.warning("PyTorch not available, falling back to CPU for OCR processing")
    return False, "cpu"


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
            [tesseract_path, "--version"], capture_output=True, text=True, timeout=10
        )
        version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
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
            [tesseract_path, "--list-langs"], capture_output=True, text=True, timeout=10
        )
        # Parse output - first line is header, rest are language codes
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            return [lang.strip() for lang in lines[1:] if lang.strip()]
        return []
    except Exception as e:
        logger.warning(f"Failed to get available OCR languages: {e}")
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
        "marathi": "mar",
        "mr": "mar",
        "hindi": "hin",
        "hi": "hin",
        "english": "eng",
        "en": "eng",
        "devanagari": "mar+hin",  # Combined for scripts
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

        self._doc: fitz.Document | None = None

    def __enter__(self) -> "OCRParser":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def open(self, password: str | None = None) -> None:
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
        full_text = pytesseract.image_to_string(img, lang=self.lang, config=config)

        # Get detailed word/line data with bounding boxes
        try:
            ocr_data = pytesseract.image_to_data(
                img, lang=self.lang, config=config, output_type=pytesseract.Output.DICT
            )

            word_data = []
            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i].strip()
                if text:
                    word_data.append(
                        {
                            "text": text,
                            "left": ocr_data["left"][i],
                            "top": ocr_data["top"][i],
                            "width": ocr_data["width"][i],
                            "height": ocr_data["height"][i],
                            "conf": ocr_data["conf"][i],
                            "line_num": ocr_data["line_num"][i],
                            "block_num": ocr_data["block_num"][i],
                        }
                    )
        except Exception as e:
            # Fall back to simple text extraction without bounding boxes
            logger.warning(
                f"Failed to extract word-level OCR data, falling back to flowing text mode: {e}"
            )
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
        self, word_data: list[dict], page_rect: fitz.Rect
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
            key = (word["block_num"], word["line_num"])
            if key not in blocks_dict:
                blocks_dict[key] = []
            blocks_dict[key].append(word)

        # Convert to TextBlock objects
        text_blocks = []
        for (_block_num, _line_num), words in sorted(blocks_dict.items()):
            line_text = " ".join(w["text"] for w in words)

            # Calculate bounding box
            min_left = min(w["left"] for w in words)
            min_top = min(w["top"] for w in words)
            max_right = max(w["left"] + w["width"] for w in words)
            max_bottom = max(w["top"] + w["height"] for w in words)

            # Average confidence
            confidences = [w["conf"] for w in words if w["conf"] >= 0]
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

    def parse(self, password: str | None = None) -> PDFDocument:
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
    filepath: Path | str, lang: str = "mar", dpi: int = 300, password: str | None = None
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


class GoogleVisionOCRParser:
    """OCR parser using Google Cloud Vision API.

    This uses the same technology as Google Translate's camera feature,
    which can properly recognize Devanagari glyphs from legacy fonts
    that render incorrectly with standard text extraction.

    Requires:
        - google-cloud-vision package: pip install google-cloud-vision
        - Google Cloud credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
        - Vision API enabled in Google Cloud project

    Cost: ~$1.50 per 1000 pages (see Google Cloud Vision pricing for current rates)
    """

    # Default DPI for rendering PDF pages to images
    DEFAULT_DPI = 300

    # Language hints for Indian languages
    LANGUAGE_HINTS = {
        "marathi": ["mr", "hi"],  # Marathi with Hindi fallback
        "mr": ["mr", "hi"],
        "mar": ["mr", "hi"],
        "hindi": ["hi"],
        "hi": ["hi"],
        "hin": ["hi"],
        "tamil": ["ta"],
        "ta": ["ta"],
        "tam": ["ta"],
        "telugu": ["te"],
        "te": ["te"],
        "tel": ["te"],
        "kannada": ["kn"],
        "kn": ["kn"],
        "kan": ["kn"],
        "malayalam": ["ml"],
        "ml": ["ml"],
        "mal": ["ml"],
        "bengali": ["bn"],
        "bn": ["bn"],
        "ben": ["bn"],
        "gujarati": ["gu"],
        "gu": ["gu"],
        "guj": ["gu"],
        "punjabi": ["pa"],
        "pa": ["pa"],
        "pan": ["pa"],
        "devanagari": ["mr", "hi", "sa"],  # Devanagari scripts
    }

    def __init__(
        self,
        filepath: Path | str,
        lang: str = "mr",
        dpi: int = DEFAULT_DPI,
    ):
        """Initialize the Google Vision OCR parser.

        Args:
            filepath: Path to the PDF file.
            lang: Language hint for OCR (e.g., 'mr' for Marathi).
            dpi: DPI for rendering PDF pages to images.

        Raises:
            OCRError: If file doesn't exist, isn't a PDF, or Vision API unavailable.
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise OCRError(f"File not found: {self.filepath}")
        if not self.filepath.suffix.lower() == ".pdf":
            raise OCRError(f"Not a PDF file: {self.filepath}")

        if not GOOGLE_VISION_AVAILABLE:
            raise OCRError(
                "google-cloud-vision not installed. Install with: pip install google-cloud-vision"
            )

        # Get language hints
        lang_lower = lang.lower()
        self.language_hints = self.LANGUAGE_HINTS.get(lang_lower, [lang_lower])
        self.dpi = dpi

        # Initialize Vision client
        try:
            self._client = vision.ImageAnnotatorClient()
        except Exception as e:
            raise OCRError(
                f"Failed to initialize Google Vision client: {e}\n"
                "Make sure GOOGLE_APPLICATION_CREDENTIALS is set to your service account key file."
            )

        self._doc: fitz.Document | None = None

    def __enter__(self) -> "GoogleVisionOCRParser":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def open(self, password: str | None = None) -> None:
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

    def render_page_to_bytes(self, page_number: int) -> bytes:
        """Render a PDF page to PNG bytes.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            PNG image bytes.
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

        # Return as PNG bytes
        return pixmap.tobytes("png")

    def ocr_page(self, page_number: int) -> tuple[str, list[dict]]:
        """Perform OCR on a single page using Google Cloud Vision.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            Tuple of (full_text, word_data) where word_data contains
            bounding box information for each word.
        """
        # Render page to PNG bytes
        image_bytes = self.render_page_to_bytes(page_number)

        # Create Vision API image
        image = vision.Image(content=image_bytes)

        # Configure image context with language hints
        image_context = vision.ImageContext(language_hints=self.language_hints)

        # Perform document text detection (better for dense text)
        try:
            response = self._client.document_text_detection(
                image=image, image_context=image_context
            )
        except Exception as e:
            raise OCRError(f"Google Vision API error: {e}")

        if response.error.message:
            raise OCRError(f"Google Vision API error: {response.error.message}")

        # Extract full text
        full_text = ""
        if response.full_text_annotation:
            full_text = response.full_text_annotation.text

        # Extract word-level data with bounding boxes
        word_data = []
        if response.full_text_annotation:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_num = len(word_data) // 100  # Approximate block grouping
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = "".join(symbol.text for symbol in word.symbols)

                            # Get bounding box
                            vertices = word.bounding_box.vertices
                            if len(vertices) >= 4:
                                left = min(v.x for v in vertices)
                                top = min(v.y for v in vertices)
                                right = max(v.x for v in vertices)
                                bottom = max(v.y for v in vertices)

                                # Get confidence
                                conf = word.confidence * 100 if hasattr(word, "confidence") else 90

                                word_data.append(
                                    {
                                        "text": word_text,
                                        "left": left,
                                        "top": top,
                                        "width": right - left,
                                        "height": bottom - top,
                                        "conf": conf,
                                        "block_num": block_num,
                                        "line_num": 0,  # Vision API doesn't provide line numbers
                                    }
                                )

        return full_text, word_data

    def parse_page(self, page_number: int) -> PDFPage:
        """Parse a single page using Google Cloud Vision OCR.

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
            # Group words into text blocks
            blocks = self._group_words_into_blocks(word_data, rect)
            pdf_page.text_blocks = blocks
        elif full_text.strip():
            # Fall back to single text block
            pdf_page.text_blocks = [
                TextBlock(
                    raw_text=full_text.strip(),
                    unicode_text=full_text.strip(),  # OCR output is already Unicode
                    confidence=0.9,  # High confidence for Google Vision
                )
            ]

        return pdf_page

    def _group_words_into_blocks(
        self, word_data: list[dict], page_rect: fitz.Rect
    ) -> list[TextBlock]:
        """Group OCR words into text blocks by proximity.

        Args:
            word_data: List of word dictionaries from OCR.
            page_rect: Page rectangle for coordinate scaling.

        Returns:
            List of TextBlock objects.
        """
        if not word_data:
            return []

        # Scale factor from image coordinates to PDF coordinates
        # Google Vision returns pixel coordinates based on the rendered image
        scale_x = page_rect.width / (self.dpi / 72.0 * page_rect.width)
        scale_y = page_rect.height / (self.dpi / 72.0 * page_rect.height)

        # Group words into lines based on vertical proximity
        # Sort by top coordinate first
        sorted_words = sorted(word_data, key=lambda w: (w["top"], w["left"]))

        lines: list[list[dict]] = []
        current_line: list[dict] = []
        last_top = -1
        line_threshold = 20  # Pixels threshold for same line

        for word in sorted_words:
            if last_top < 0 or abs(word["top"] - last_top) <= line_threshold:
                current_line.append(word)
            else:
                if current_line:
                    # Sort line by horizontal position
                    current_line.sort(key=lambda w: w["left"])
                    lines.append(current_line)
                current_line = [word]
            last_top = word["top"]

        if current_line:
            current_line.sort(key=lambda w: w["left"])
            lines.append(current_line)

        # Convert lines to TextBlock objects
        text_blocks = []
        for line_words in lines:
            if not line_words:
                continue

            line_text = " ".join(w["text"] for w in line_words)

            # Calculate bounding box
            min_left = min(w["left"] for w in line_words)
            min_top = min(w["top"] for w in line_words)
            max_right = max(w["left"] + w["width"] for w in line_words)
            max_bottom = max(w["top"] + w["height"] for w in line_words)

            # Average confidence
            confidences = [w["conf"] for w in line_words if w["conf"] >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 90.0

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
                    confidence=avg_conf / 100.0,
                )
            )

        return text_blocks

    def parse(self, password: str | None = None) -> PDFDocument:
        """Parse the entire PDF using Google Cloud Vision OCR.

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


def parse_pdf_with_google_vision(
    filepath: Path | str, lang: str = "mr", dpi: int = 300, password: str | None = None
) -> PDFDocument:
    """Parse a PDF using Google Cloud Vision OCR.

    This is the recommended method for PDFs with legacy Indian fonts
    that render incorrectly with standard text extraction.

    Args:
        filepath: Path to the PDF file.
        lang: Language hint (e.g., 'mr' for Marathi, 'hi' for Hindi).
        dpi: DPI for rendering (higher = better quality but slower).
        password: Password for encrypted PDFs.

    Returns:
        PDFDocument with OCR-extracted text in proper Unicode.

    Requires:
        - google-cloud-vision package
        - GOOGLE_APPLICATION_CREDENTIALS environment variable set
        - Vision API enabled in Google Cloud project
    """
    with GoogleVisionOCRParser(filepath, lang=lang, dpi=dpi) as parser:
        return parser.parse(password)


def check_google_vision_available() -> tuple[bool, str]:
    """Check if Google Cloud Vision is available and configured.

    Returns:
        Tuple of (is_available, message).
    """
    if not GOOGLE_VISION_AVAILABLE:
        return (
            False,
            "google-cloud-vision not installed. Install with: pip install google-cloud-vision",
        )

    import os

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return False, (
            "GOOGLE_APPLICATION_CREDENTIALS not set. "
            "Set it to the path of your service account key JSON file."
        )

    try:
        vision.ImageAnnotatorClient()
        return True, "Google Cloud Vision is available and configured"
    except Exception as e:
        return False, f"Failed to initialize Google Vision client: {e}"


class EasyOCRParser:
    """OCR parser using EasyOCR - completely free, no API keys required.

    EasyOCR uses deep learning (PyTorch) for text recognition and supports
    80+ languages including Marathi, Hindi, and other Indian languages.
    It runs entirely locally with no cloud dependencies.

    This is the recommended FREE solution for PDFs with legacy Indian fonts.

    Install: pip install easyocr
    First run downloads language models (~100MB per language).
    """

    # Default DPI for rendering PDF pages to images
    DEFAULT_DPI = 300

    # Language codes mapping
    LANGUAGE_CODES = {
        "marathi": ["mr", "en"],  # Marathi + English fallback
        "mr": ["mr", "en"],
        "mar": ["mr", "en"],
        "hindi": ["hi", "en"],
        "hi": ["hi", "en"],
        "hin": ["hi", "en"],
        "tamil": ["ta", "en"],
        "ta": ["ta", "en"],
        "tam": ["ta", "en"],
        "telugu": ["te", "en"],
        "te": ["te", "en"],
        "tel": ["te", "en"],
        "kannada": ["kn", "en"],
        "kn": ["kn", "en"],
        "kan": ["kn", "en"],
        "malayalam": ["ml", "en"],
        "ml": ["ml", "en"],
        "mal": ["ml", "en"],
        "bengali": ["bn", "en"],
        "bn": ["bn", "en"],
        "ben": ["bn", "en"],
        "gujarati": ["gu", "en"],
        "gu": ["gu", "en"],
        "guj": ["gu", "en"],
        "punjabi": ["pa", "en"],
        "pa": ["pa", "en"],
        "pan": ["pa", "en"],
        "devanagari": ["hi", "mr", "en"],  # Hindi + Marathi for Devanagari
        "english": ["en"],
        "en": ["en"],
        "eng": ["en"],
    }

    def __init__(
        self,
        filepath: Path | str,
        lang: str = "mr",
        dpi: int = DEFAULT_DPI,
        gpu: bool | str = "auto",  # "auto" detects CUDA/MPS, or explicit True/False
    ):
        """Initialize the EasyOCR parser.

        Args:
            filepath: Path to the PDF file.
            lang: Language code (e.g., 'mr' for Marathi, 'hi' for Hindi).
            dpi: DPI for rendering PDF pages to images.
            gpu: GPU acceleration mode:
                - "auto": Auto-detect CUDA (NVIDIA) or MPS (Apple Silicon)
                - True: Force GPU usage
                - False: Force CPU usage

        Raises:
            OCRError: If file doesn't exist, isn't a PDF, or EasyOCR unavailable.
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise OCRError(f"File not found: {self.filepath}")
        if not self.filepath.suffix.lower() == ".pdf":
            raise OCRError(f"Not a PDF file: {self.filepath}")

        if not EASYOCR_AVAILABLE:
            raise OCRError(
                "easyocr not installed. Install with: pip install easyocr\n"
                "Note: First run will download language models (~100MB per language)."
            )

        # Get language codes for EasyOCR
        lang_lower = lang.lower()
        self.languages = self.LANGUAGE_CODES.get(lang_lower, ["en"])
        self.dpi = dpi

        # Auto-detect GPU backend
        if gpu == "auto":
            gpu_available, backend = detect_gpu_backend()
            self.gpu = gpu_available
            self._gpu_backend = backend
        else:
            self.gpu = bool(gpu)
            self._gpu_backend = "cuda" if self.gpu else "cpu"

        # Initialize EasyOCR reader (lazy - downloads models on first use)
        try:
            import logging

            ocr_logger = logging.getLogger(__name__)
            ocr_logger.info(
                f"Initializing EasyOCR with GPU={self.gpu} (backend: {self._gpu_backend})"
            )
            self._reader = easyocr.Reader(self.languages, gpu=self.gpu)
        except Exception as e:
            raise OCRError(f"Failed to initialize EasyOCR: {e}")

        self._doc: fitz.Document | None = None

    def __enter__(self) -> "EasyOCRParser":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def open(self, password: str | None = None) -> None:
        """Open the PDF document."""
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
        """Extract document metadata."""
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

    def render_page_to_numpy(self, page_number: int) -> "np.ndarray":
        """Render a PDF page to a numpy array for EasyOCR.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            Numpy array of the page image (RGB).
        """
        import numpy as np

        if page_number < 0 or page_number >= len(self.doc):
            raise OCRError(
                f"Invalid page number: {page_number}. Document has {len(self.doc)} pages."
            )

        page = self.doc[page_number]

        # Calculate zoom factor for desired DPI
        zoom = self.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to numpy array
        img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
        img_array = img_array.reshape(pixmap.height, pixmap.width, 3)

        return img_array

    def ocr_page(self, page_number: int) -> tuple[str, list[dict]]:
        """Perform OCR on a single page using EasyOCR.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            Tuple of (full_text, word_data) where word_data contains
            bounding box information for each detected text region.
        """
        # Render page to numpy array
        img_array = self.render_page_to_numpy(page_number)

        # Run EasyOCR
        # Returns list of (bbox, text, confidence) tuples
        # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
        results = self._reader.readtext(img_array)

        word_data = []
        text_parts = []

        for bbox, text, confidence in results:
            if text.strip():
                text_parts.append(text)

                # Extract bounding box coordinates
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                left = min(x_coords)
                top = min(y_coords)
                right = max(x_coords)
                bottom = max(y_coords)

                word_data.append(
                    {
                        "text": text,
                        "left": left,
                        "top": top,
                        "width": right - left,
                        "height": bottom - top,
                        "conf": confidence * 100,  # Convert to 0-100 scale
                        "block_num": 0,
                        "line_num": 0,
                    }
                )

        full_text = " ".join(text_parts)
        return full_text, word_data

    def parse_page(self, page_number: int) -> PDFPage:
        """Parse a single page using EasyOCR.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            PDFPage object with extracted text blocks.
        """
        page = self.doc[page_number]
        rect = page.rect

        pdf_page = PDFPage(
            page_number=page_number + 1,
            width=rect.width,
            height=rect.height,
        )

        # Perform OCR
        full_text, word_data = self.ocr_page(page_number)

        if word_data:
            # Group words into text blocks by line proximity
            blocks = self._group_words_into_blocks(word_data, rect)
            pdf_page.text_blocks = blocks
        elif full_text.strip():
            pdf_page.text_blocks = [
                TextBlock(
                    raw_text=full_text.strip(),
                    unicode_text=full_text.strip(),
                    confidence=0.85,
                )
            ]

        return pdf_page

    def _group_words_into_blocks(
        self, word_data: list[dict], page_rect: fitz.Rect
    ) -> list[TextBlock]:
        """Group OCR words into text blocks by proximity."""
        if not word_data:
            return []

        # Scale factor from image to PDF coordinates
        scale_x = page_rect.width / (self.dpi / 72.0 * page_rect.width)
        scale_y = page_rect.height / (self.dpi / 72.0 * page_rect.height)

        # Sort by vertical position then horizontal
        sorted_words = sorted(word_data, key=lambda w: (w["top"], w["left"]))

        # Group into lines
        lines: list[list[dict]] = []
        current_line: list[dict] = []
        last_top = -1
        # EasyOCR uses larger text regions than Google Vision, so use a larger
        # threshold (30px vs 20px in GoogleVisionOCRParser) to group words into lines
        line_threshold = 30

        for word in sorted_words:
            if last_top < 0 or abs(word["top"] - last_top) <= line_threshold:
                current_line.append(word)
            else:
                if current_line:
                    current_line.sort(key=lambda w: w["left"])
                    lines.append(current_line)
                current_line = [word]
            last_top = word["top"]

        if current_line:
            current_line.sort(key=lambda w: w["left"])
            lines.append(current_line)

        # Convert to TextBlocks
        text_blocks = []
        for line_words in lines:
            if not line_words:
                continue

            line_text = " ".join(w["text"] for w in line_words)

            min_left = min(w["left"] for w in line_words)
            min_top = min(w["top"] for w in line_words)
            max_right = max(w["left"] + w["width"] for w in line_words)
            max_bottom = max(w["top"] + w["height"] for w in line_words)

            confidences = [w["conf"] for w in line_words if w["conf"] >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 85.0

            text_blocks.append(
                TextBlock(
                    raw_text=line_text,
                    unicode_text=line_text,
                    position=BoundingBox(
                        x0=min_left * scale_x,
                        y0=min_top * scale_y,
                        x1=max_right * scale_x,
                        y1=max_bottom * scale_y,
                    ),
                    confidence=avg_conf / 100.0,
                )
            )

        return text_blocks

    def parse(self, password: str | None = None) -> PDFDocument:
        """Parse the entire PDF using EasyOCR.

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
                fonts=[],
            )
        finally:
            if need_close:
                self.close()


def parse_pdf_with_easyocr(
    filepath: Path | str,
    lang: str = "mr",
    dpi: int = 300,
    gpu: bool | str = "auto",
    password: str | None = None,
) -> PDFDocument:
    """Parse a PDF using EasyOCR - completely FREE, no API keys needed.

    This is the recommended method for PDFs with legacy Indian fonts
    when you don't want to use paid cloud services.

    Args:
        filepath: Path to the PDF file.
        lang: Language code (e.g., 'mr' for Marathi, 'hi' for Hindi).
        dpi: DPI for rendering (higher = better quality but slower).
        gpu: GPU acceleration mode:
            - "auto" (default): Auto-detect CUDA (NVIDIA) or MPS (Apple Silicon)
            - True: Force GPU usage
            - False: Force CPU usage
        password: Password for encrypted PDFs.

    Returns:
        PDFDocument with OCR-extracted Unicode text.

    Note:
        First run downloads language models (~100MB per language).
        On Apple Silicon Macs, MPS acceleration is automatically enabled.
    """
    with EasyOCRParser(filepath, lang=lang, dpi=dpi, gpu=gpu) as parser:
        return parser.parse(password)


def check_easyocr_available() -> tuple[bool, str]:
    """Check if EasyOCR is available.

    Returns:
        Tuple of (is_available, message).
    """
    if not EASYOCR_AVAILABLE:
        return False, "easyocr not installed. Install with: pip install easyocr"

    return True, "EasyOCR is available (free, no API key needed)"
