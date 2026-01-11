"""PDF Parser module for extracting text and font metadata.

This module uses PyMuPDF (fitz) to extract text content, font information,
and positional metadata from PDF documents.
"""

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from legacylipi.core.models import (
    BoundingBox,
    DocumentMetadata,
    FontInfo,
    PDFDocument,
    PDFPage,
    TextBlock,
)


class PDFParseError(Exception):
    """Exception raised when PDF parsing fails."""

    pass


class PDFParser:
    """Parser for extracting text and font information from PDF documents."""

    def __init__(self, filepath: Path | str):
        """Initialize the PDF parser.

        Args:
            filepath: Path to the PDF file to parse.

        Raises:
            PDFParseError: If the file doesn't exist or cannot be opened.
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise PDFParseError(f"File not found: {self.filepath}")
        if not self.filepath.suffix.lower() == ".pdf":
            raise PDFParseError(f"Not a PDF file: {self.filepath}")

        self._doc: Optional[fitz.Document] = None

    def __enter__(self) -> "PDFParser":
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

        Raises:
            PDFParseError: If the document cannot be opened.
        """
        try:
            self._doc = fitz.open(self.filepath)
            if self._doc.is_encrypted:
                if password:
                    if not self._doc.authenticate(password):
                        raise PDFParseError("Invalid password for encrypted PDF")
                else:
                    raise PDFParseError("PDF is encrypted. Password required.")
        except fitz.FileDataError as e:
            raise PDFParseError(f"Invalid PDF file: {e}")
        except Exception as e:
            raise PDFParseError(f"Failed to open PDF: {e}")

    def close(self) -> None:
        """Close the PDF document."""
        if self._doc:
            self._doc.close()
            self._doc = None

    @property
    def doc(self) -> fitz.Document:
        """Get the underlying fitz document.

        Raises:
            PDFParseError: If the document is not open.
        """
        if self._doc is None:
            raise PDFParseError("Document not open. Call open() first.")
        return self._doc

    def get_metadata(self) -> DocumentMetadata:
        """Extract document metadata.

        Returns:
            DocumentMetadata object with available metadata.
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

    def get_fonts(self) -> list[FontInfo]:
        """Extract all fonts used in the document.

        Returns:
            List of FontInfo objects for all fonts in the document.
        """
        fonts: set[FontInfo] = set()
        for page in self.doc:
            page_fonts = self._extract_page_fonts(page)
            fonts.update(page_fonts)
        return list(fonts)

    def _extract_page_fonts(self, page: fitz.Page) -> list[FontInfo]:
        """Extract fonts from a single page.

        Args:
            page: The page to extract fonts from.

        Returns:
            List of FontInfo objects.
        """
        fonts = []
        try:
            font_list = page.get_fonts(full=True)
            for font in font_list:
                # font tuple: (xref, ext, type, basefont, name, encoding, ...)
                xref = font[0]
                font_type = font[2]
                basefont = font[3]
                name = font[4]
                encoding = font[5] if len(font) > 5 else None

                # Determine if font is embedded
                is_embedded = xref > 0 and font_type not in ("Type1", "Type3")

                # Check if it's a subset (subset names usually start with random prefix + '+')
                is_subset = "+" in name if name else False

                fonts.append(
                    FontInfo(
                        name=basefont or name or "Unknown",
                        encoding=encoding,
                        is_embedded=is_embedded,
                        is_subset=is_subset,
                    )
                )
        except Exception:
            # If font extraction fails, continue without font info
            pass
        return fonts

    def parse_page(self, page_number: int) -> PDFPage:
        """Parse a single page of the PDF.

        Args:
            page_number: Zero-indexed page number.

        Returns:
            PDFPage object with extracted text blocks.

        Raises:
            PDFParseError: If the page number is invalid.
        """
        if page_number < 0 or page_number >= len(self.doc):
            raise PDFParseError(
                f"Invalid page number: {page_number}. Document has {len(self.doc)} pages."
            )

        page = self.doc[page_number]
        rect = page.rect

        pdf_page = PDFPage(
            page_number=page_number + 1,  # 1-indexed for user-facing
            width=rect.width,
            height=rect.height,
        )

        # Extract text blocks with font information
        text_blocks = self._extract_text_blocks(page)
        pdf_page.text_blocks = text_blocks

        return pdf_page

    def _extract_text_blocks(self, page: fitz.Page) -> list[TextBlock]:
        """Extract text blocks from a page with font information.

        Args:
            page: The page to extract text from.

        Returns:
            List of TextBlock objects.
        """
        blocks = []

        # Use "dict" extraction for detailed information including fonts
        try:
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        except Exception:
            # Fall back to simple text extraction
            simple_text = page.get_text("text")
            if simple_text.strip():
                blocks.append(TextBlock(raw_text=simple_text.strip()))
            return blocks

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # Skip non-text blocks (images, etc.)
                continue

            for line in block.get("lines", []):
                line_text = ""
                line_font = None
                line_size = 12.0
                x0, y0, x1, y1 = float("inf"), float("inf"), 0, 0

                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if text:
                        line_text += text
                        # Get font info from first span with text
                        if line_font is None:
                            line_font = span.get("font")
                            line_size = span.get("size", 12.0)

                        # Update bounding box
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        x0 = min(x0, bbox[0])
                        y0 = min(y0, bbox[1])
                        x1 = max(x1, bbox[2])
                        y1 = max(y1, bbox[3])

                if line_text.strip():
                    # Normalize infinite values
                    if x0 == float("inf"):
                        x0, y0, x1, y1 = 0, 0, 0, 0

                    blocks.append(
                        TextBlock(
                            raw_text=line_text,
                            font_name=line_font,
                            font_size=line_size,
                            position=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
                        )
                    )

        return blocks

    def parse(self, password: Optional[str] = None) -> PDFDocument:
        """Parse the entire PDF document.

        Args:
            password: Password for encrypted PDFs.

        Returns:
            PDFDocument object with all pages and metadata.
        """
        need_close = False
        if self._doc is None:
            self.open(password)
            need_close = True

        try:
            # Get metadata and fonts
            metadata = self.get_metadata()
            fonts = self.get_fonts()

            # Parse all pages
            pages = []
            for i in range(len(self.doc)):
                page = self.parse_page(i)
                pages.append(page)

            return PDFDocument(
                filepath=self.filepath,
                pages=pages,
                metadata=metadata,
                fonts=fonts,
            )
        finally:
            if need_close:
                self.close()


def parse_pdf(filepath: Path | str, password: Optional[str] = None) -> PDFDocument:
    """Convenience function to parse a PDF document.

    Args:
        filepath: Path to the PDF file.
        password: Password for encrypted PDFs.

    Returns:
        PDFDocument object with all pages and metadata.
    """
    with PDFParser(filepath) as parser:
        return parser.parse(password)
