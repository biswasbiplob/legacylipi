"""Output Generator module for creating translated document outputs.

This module handles generating various output formats from translated content,
including plain text, Markdown, PDF, and side-by-side bilingual documents.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import fitz  # PyMuPDF

from legacylipi.core.models import (
    EncodingDetectionResult,
    OutputFormat,
    PDFDocument,
    TranslationResult,
)


@dataclass
class OutputMetadata:
    """Metadata to include in output files."""

    source_file: str
    encoding_detected: str
    encoding_confidence: float
    source_language: str
    target_language: str
    translation_backend: str
    generated_at: str
    page_count: int


class OutputGenerator:
    """Generator for various output formats."""

    def __init__(
        self,
        include_metadata: bool = True,
        include_page_numbers: bool = True,
    ):
        """Initialize the output generator.

        Args:
            include_metadata: Whether to include metadata header in output.
            include_page_numbers: Whether to include page number markers.
        """
        self._include_metadata = include_metadata
        self._include_page_numbers = include_page_numbers

    def generate_metadata(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: Optional[TranslationResult] = None,
    ) -> OutputMetadata:
        """Generate metadata for output files.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result (if available).

        Returns:
            OutputMetadata with document information.
        """
        return OutputMetadata(
            source_file=document.filepath.name,
            encoding_detected=encoding_result.detected_encoding,
            encoding_confidence=encoding_result.confidence,
            source_language=translation_result.source_language if translation_result else "unknown",
            target_language=translation_result.target_language if translation_result else "unknown",
            translation_backend=translation_result.translation_backend.value if translation_result else "none",
            generated_at=datetime.now().isoformat(),
            page_count=document.page_count,
        )

    def generate_text(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: Optional[TranslationResult] = None,
        translated_text: Optional[str] = None,
    ) -> str:
        """Generate plain text output.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.
            translated_text: Translated text to use (overrides translation_result).

        Returns:
            Plain text output string.
        """
        lines = []

        # Add metadata header if enabled
        if self._include_metadata:
            metadata = self.generate_metadata(document, encoding_result, translation_result)
            lines.append(self._format_text_header(metadata))
            lines.append("")
            lines.append("=" * 60)
            lines.append("")

        # Get the translated text
        if translated_text:
            content = translated_text
        elif translation_result:
            content = translation_result.translated_text
        else:
            # Use Unicode text from document
            content = document.unicode_text

        # Add page markers if enabled
        if self._include_page_numbers and len(document.pages) > 1:
            lines.append(self._format_text_with_pages(document, translation_result))
        else:
            lines.append(content)

        return "\n".join(lines)

    def _format_text_header(self, metadata: OutputMetadata) -> str:
        """Format metadata as a text header.

        Args:
            metadata: Output metadata.

        Returns:
            Formatted header string.
        """
        return f"""LegacyLipi Translation Output
=============================
Source File: {metadata.source_file}
Encoding: {metadata.encoding_detected} (confidence: {metadata.encoding_confidence:.1%})
Languages: {metadata.source_language} → {metadata.target_language}
Backend: {metadata.translation_backend}
Pages: {metadata.page_count}
Generated: {metadata.generated_at}"""

    def _format_text_with_pages(
        self,
        document: PDFDocument,
        translation_result: Optional[TranslationResult],
    ) -> str:
        """Format text with page markers.

        Args:
            document: The processed document.
            translation_result: Translation result for chunked content.

        Returns:
            Formatted text with page markers.
        """
        lines = []

        for page in document.pages:
            lines.append(f"--- Page {page.page_number} ---")
            lines.append("")
            lines.append(page.unicode_text)
            lines.append("")

        return "\n".join(lines)

    def generate_markdown(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: Optional[TranslationResult] = None,
        translated_text: Optional[str] = None,
    ) -> str:
        """Generate Markdown output.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.
            translated_text: Translated text to use.

        Returns:
            Markdown formatted output string.
        """
        lines = []

        # Add metadata header
        if self._include_metadata:
            metadata = self.generate_metadata(document, encoding_result, translation_result)
            lines.append(self._format_markdown_header(metadata))
            lines.append("")
            lines.append("---")
            lines.append("")

        # Get the translated text
        if translated_text:
            content = translated_text
        elif translation_result:
            content = translation_result.translated_text
        else:
            content = document.unicode_text

        # Add content with page headers if enabled
        if self._include_page_numbers and len(document.pages) > 1:
            lines.append(self._format_markdown_with_pages(document, translation_result))
        else:
            lines.append(content)

        return "\n".join(lines)

    def _format_markdown_header(self, metadata: OutputMetadata) -> str:
        """Format metadata as Markdown header.

        Args:
            metadata: Output metadata.

        Returns:
            Markdown formatted header.
        """
        return f"""# Translation: {metadata.source_file}

| Property | Value |
|----------|-------|
| Source File | `{metadata.source_file}` |
| Encoding | {metadata.encoding_detected} |
| Confidence | {metadata.encoding_confidence:.1%} |
| Languages | {metadata.source_language} → {metadata.target_language} |
| Backend | {metadata.translation_backend} |
| Pages | {metadata.page_count} |
| Generated | {metadata.generated_at} |"""

    def _format_markdown_with_pages(
        self,
        document: PDFDocument,
        translation_result: Optional[TranslationResult],
    ) -> str:
        """Format content with Markdown page headers.

        Args:
            document: The processed document.
            translation_result: Translation result.

        Returns:
            Markdown formatted content with page headers.
        """
        lines = []

        for page in document.pages:
            lines.append(f"## Page {page.page_number}")
            lines.append("")
            lines.append(page.unicode_text)
            lines.append("")

        return "\n".join(lines)

    def generate_bilingual(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: TranslationResult,
    ) -> str:
        """Generate side-by-side bilingual Markdown output.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.

        Returns:
            Markdown with original and translated text side by side.
        """
        lines = []

        if self._include_metadata:
            metadata = self.generate_metadata(document, encoding_result, translation_result)
            lines.append(self._format_markdown_header(metadata))
            lines.append("")
            lines.append("---")
            lines.append("")

        # Add bilingual content
        lines.append("## Bilingual Content")
        lines.append("")

        # Get source and translated texts
        source_text = document.unicode_text
        translated_text = translation_result.translated_text

        # Split into paragraphs for side-by-side display
        source_paras = source_text.split("\n\n")
        translated_paras = translated_text.split("\n\n")

        # Create table
        lines.append("| Original | Translation |")
        lines.append("|----------|-------------|")

        max_paras = max(len(source_paras), len(translated_paras))
        for i in range(max_paras):
            source = source_paras[i] if i < len(source_paras) else ""
            translated = translated_paras[i] if i < len(translated_paras) else ""

            # Escape pipe characters for table
            source = source.replace("|", "\\|").replace("\n", " ")
            translated = translated.replace("|", "\\|").replace("\n", " ")

            lines.append(f"| {source} | {translated} |")

        return "\n".join(lines)

    def generate_pdf(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: Optional[TranslationResult] = None,
        translated_text: Optional[str] = None,
        output_path: Optional[Path] = None,
        preserve_structure: bool = True,
    ) -> bytes:
        """Generate PDF output preserving document structure.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.
            translated_text: Translated text to use (overrides translation_result).
            output_path: Optional path to save PDF directly.
            preserve_structure: If True, preserve original page dimensions and text positions.

        Returns:
            PDF content as bytes.
        """
        # Create a new PDF document
        pdf_doc = fitz.open()

        # Get metadata for header
        metadata = self.generate_metadata(document, encoding_result, translation_result)

        # Find a font that supports the content
        font_path = self._get_unicode_font()

        # Only preserve structure when NOT translating - translated text has different
        # length and structure, so we must use flowing A4 layout for translations
        if preserve_structure and translation_result is None and translated_text is None:
            # Generate PDF preserving original structure (extraction only)
            return self._generate_pdf_preserve_structure(
                pdf_doc, document, metadata, translation_result,
                translated_text, output_path, font_path
            )
        else:
            # Generate PDF with standard A4 layout (for translations or explicit request)
            return self._generate_pdf_a4_layout(
                pdf_doc, document, metadata, translation_result,
                translated_text, output_path, font_path
            )

    def _generate_pdf_preserve_structure(
        self,
        pdf_doc: fitz.Document,
        document: PDFDocument,
        metadata: OutputMetadata,
        translation_result: Optional[TranslationResult],
        translated_text: Optional[str],
        output_path: Optional[Path],
        font_path: Optional[str],
    ) -> bytes:
        """Generate PDF preserving original page dimensions and text positions.

        Args:
            pdf_doc: The fitz document to write to.
            document: The processed PDF document.
            metadata: Output metadata.
            translation_result: Translation result.
            translated_text: Translated text override.
            output_path: Optional path to save PDF.
            font_path: Path to Unicode font.

        Returns:
            PDF content as bytes.
        """
        # Add metadata page if enabled (using first page's dimensions)
        if self._include_metadata and document.pages:
            first_page = document.pages[0]
            page_width = first_page.width if first_page.width > 0 else 595
            page_height = first_page.height if first_page.height > 0 else 842
            meta_page = pdf_doc.new_page(width=page_width, height=page_height)
            margin = min(50, page_width * 0.08)
            self._add_metadata_to_pdf_page(meta_page, metadata, margin, 11, font_path)

        # Process each page from the source document
        for page_data in document.pages:
            # Use original page dimensions
            page_width = page_data.width if page_data.width > 0 else 595
            page_height = page_data.height if page_data.height > 0 else 842

            # Create a new page with original dimensions
            new_page = pdf_doc.new_page(width=page_width, height=page_height)

            # Check if we have text blocks with positions
            if page_data.text_blocks and any(b.position for b in page_data.text_blocks):
                # Place text blocks at their original positions
                self._place_text_blocks_with_positions(
                    new_page, page_data.text_blocks, font_path
                )
            else:
                # Fallback to simple text layout if no position data
                margin = min(50, page_width * 0.08)
                line_height = 16
                y_position = margin

                # Add page header if enabled
                if self._include_page_numbers:
                    header_text = f"Page {page_data.page_number}"
                    self._insert_text_with_font(
                        new_page, margin, y_position, header_text,
                        9, font_path, color=(0.5, 0.5, 0.5)
                    )
                    y_position += line_height * 2

                # Add page content with word wrapping
                page_text = page_data.unicode_text
                usable_width = page_width - (2 * margin)
                lines = self._wrap_text_for_pdf(page_text, usable_width, 11)

                for line in lines:
                    if y_position > page_height - margin:
                        # Create overflow page
                        new_page = pdf_doc.new_page(width=page_width, height=page_height)
                        y_position = margin

                    self._insert_text_with_font(
                        new_page, margin, y_position, line, 11, font_path
                    )
                    y_position += line_height

        # Get PDF bytes
        pdf_bytes = pdf_doc.tobytes()

        # Optionally save to file
        if output_path:
            pdf_doc.save(output_path)

        pdf_doc.close()
        return pdf_bytes

    def _place_text_blocks_with_positions(
        self,
        page: fitz.Page,
        text_blocks: list,
        font_path: Optional[str],
    ) -> None:
        """Place text blocks at their original positions on a page.

        Args:
            page: The fitz page to write to.
            text_blocks: List of TextBlock objects with position data.
            font_path: Path to Unicode font.
        """
        for block in text_blocks:
            # Get text (prefer unicode_text if available)
            text = block.unicode_text if block.unicode_text else block.raw_text
            if not text or not text.strip():
                continue

            # Get position
            if block.position:
                x = block.position.x0
                # Adjust y to account for font baseline (add font size)
                y = block.position.y0 + block.font_size
            else:
                # Skip blocks without position
                continue

            # Use original font size, with reasonable bounds
            font_size = block.font_size if 4 <= block.font_size <= 72 else 12

            # Insert text at original position
            self._insert_text_with_font(
                page, x, y, text.strip(), font_size, font_path
            )

    def _generate_pdf_a4_layout(
        self,
        pdf_doc: fitz.Document,
        document: PDFDocument,
        metadata: OutputMetadata,
        translation_result: Optional[TranslationResult],
        translated_text: Optional[str],
        output_path: Optional[Path],
        font_path: Optional[str],
    ) -> bytes:
        """Generate PDF preserving page structure from source document.

        When translation results are available, preserves page-to-page correspondence:
        - Each output page corresponds to the same input page
        - Uses original page dimensions
        - Scales font down if text is too long to fit

        Args:
            pdf_doc: The fitz document to write to.
            document: The processed PDF document.
            metadata: Output metadata.
            translation_result: Translation result.
            translated_text: Translated text override.
            output_path: Optional path to save PDF.
            font_path: Path to Unicode font.

        Returns:
            PDF content as bytes.
        """
        margin = 50
        base_font_size = 11
        header_font_size = 9

        # Get text content - use translated text if available
        if translated_text:
            full_text = translated_text
        elif translation_result:
            full_text = translation_result.translated_text
        else:
            full_text = document.unicode_text

        # Check if we have page markers and should preserve structure
        has_page_markers = "--- Page " in full_text
        num_pages = len(document.pages)

        if has_page_markers and num_pages > 0:
            # Page-by-page rendering preserving structure
            return self._generate_pdf_page_by_page(
                pdf_doc, document, metadata, full_text,
                output_path, font_path, margin, base_font_size, header_font_size
            )
        else:
            # Fallback to flowing A4 layout
            return self._generate_pdf_flowing_layout(
                pdf_doc, document, metadata, full_text,
                output_path, font_path, margin, base_font_size, header_font_size
            )

    def _generate_pdf_page_by_page(
        self,
        pdf_doc: fitz.Document,
        document: PDFDocument,
        metadata: OutputMetadata,
        full_text: str,
        output_path: Optional[Path],
        font_path: Optional[str],
        margin: float,
        base_font_size: float,
        header_font_size: float,
    ) -> bytes:
        """Generate PDF with page-by-page structure preservation.

        Each output page corresponds to the same input page with scaled font.
        """
        num_pages = len(document.pages)

        # Parse translated text by page markers
        page_texts = self._parse_page_markers(full_text, num_pages)

        # Add metadata page using first page's dimensions
        if self._include_metadata and document.pages:
            first_page = document.pages[0]
            meta_width = first_page.width if first_page.width > 0 else 595
            meta_height = first_page.height if first_page.height > 0 else 842
            meta_page = pdf_doc.new_page(width=meta_width, height=meta_height)
            self._add_metadata_to_pdf_page(meta_page, metadata, margin, base_font_size, font_path)

        # Generate each page preserving original dimensions
        for i, page_data in enumerate(document.pages):
            # Use original page dimensions
            page_width = page_data.width if page_data.width > 0 else 595
            page_height = page_data.height if page_data.height > 0 else 842

            # Create output page with same dimensions
            new_page = pdf_doc.new_page(width=page_width, height=page_height)

            # Get translated text for this page
            page_text = page_texts[i] if i < len(page_texts) else ""

            # Calculate font size to fit text on this page
            font_size = self._calculate_fit_font_size(
                page_text, page_width, page_height, margin, base_font_size
            )
            line_height = font_size * 1.4

            # Start rendering
            y_position = margin

            # Add page header if enabled
            if self._include_page_numbers:
                header_text = f"Page {i + 1}"
                self._insert_text_with_font(
                    new_page, margin, y_position, header_text,
                    header_font_size, font_path, color=(0.5, 0.5, 0.5)
                )
                y_position += line_height * 1.5

            # Wrap and render page text
            usable_width = page_width - (2 * margin)
            # Adjust chars per line based on font size
            chars_per_line = int(usable_width / (font_size * 0.5))
            lines = self._wrap_text_for_pdf(page_text, usable_width, font_size, chars_per_line)

            for line in lines:
                if y_position > page_height - margin:
                    # Text overflows despite font scaling - stop rendering
                    break

                self._insert_text_with_font(
                    new_page, margin, y_position, line,
                    font_size, font_path
                )
                y_position += line_height

        # Get PDF bytes
        pdf_bytes = pdf_doc.tobytes()

        if output_path:
            pdf_doc.save(output_path)

        pdf_doc.close()
        return pdf_bytes

    def _generate_pdf_flowing_layout(
        self,
        pdf_doc: fitz.Document,
        document: PDFDocument,
        metadata: OutputMetadata,
        full_text: str,
        output_path: Optional[Path],
        font_path: Optional[str],
        margin: float,
        font_size: float,
        header_font_size: float,
    ) -> bytes:
        """Generate PDF with flowing A4 layout (text flows across pages)."""
        # PDF page settings (A4)
        page_width = 595
        page_height = 842
        line_height = font_size * 1.4

        # Add metadata page if enabled
        if self._include_metadata:
            meta_page = pdf_doc.new_page(width=page_width, height=page_height)
            self._add_metadata_to_pdf_page(meta_page, metadata, margin, font_size, font_path)

        # Wrap text for rendering
        usable_width = page_width - (2 * margin)
        lines = self._wrap_text_for_pdf(full_text, usable_width, font_size)

        # Create first content page
        new_page = pdf_doc.new_page(width=page_width, height=page_height)
        y_position = margin
        page_number = 1

        # Add page header if enabled
        if self._include_page_numbers:
            header_text = f"Page {page_number}"
            self._insert_text_with_font(
                new_page, margin, y_position, header_text,
                header_font_size, font_path, color=(0.5, 0.5, 0.5)
            )
            y_position += line_height * 2

        # Add all content lines, creating new pages as needed
        for line in lines:
            if y_position > page_height - margin:
                # Create a new page if we run out of space
                new_page = pdf_doc.new_page(width=page_width, height=page_height)
                y_position = margin
                page_number += 1

                # Add page header to new page
                if self._include_page_numbers:
                    header_text = f"Page {page_number}"
                    self._insert_text_with_font(
                        new_page, margin, y_position, header_text,
                        header_font_size, font_path, color=(0.5, 0.5, 0.5)
                    )
                    y_position += line_height * 2

            # Insert text with proper font
            self._insert_text_with_font(
                new_page, margin, y_position, line,
                font_size, font_path
            )
            y_position += line_height

        # Get PDF bytes
        pdf_bytes = pdf_doc.tobytes()

        if output_path:
            pdf_doc.save(output_path)

        pdf_doc.close()
        return pdf_bytes

    def _insert_text_with_font(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        text: str,
        fontsize: float,
        font_path: Optional[str],
        color: tuple = (0, 0, 0),
    ) -> None:
        """Insert text with proper font support using TextWriter for Unicode.

        Args:
            page: The fitz Page object.
            x: X coordinate.
            y: Y coordinate.
            text: Text to insert.
            fontsize: Font size.
            font_path: Path to font file (or None for default).
            color: RGB color tuple.
        """
        if font_path and Path(font_path).exists():
            # Use TextWriter with custom font for proper Unicode support
            tw = fitz.TextWriter(page.rect)
            font = fitz.Font(fontfile=font_path)
            tw.append((x, y), text, font=font, fontsize=fontsize)
            tw.write_text(page, color=color)
        else:
            # Fallback to built-in font (limited Unicode support)
            page.insert_text(
                (x, y),
                text,
                fontsize=fontsize,
                fontname="helv",
                color=color,
            )

    def _get_unicode_font(self) -> Optional[str]:
        """Find a font that supports Unicode/Devanagari on the system.

        Returns:
            Path to a Unicode-capable font file, or None if not found.
        """
        # Common Unicode/Devanagari font paths (in order of preference)
        font_paths = [
            # Linux - Noto fonts (best Unicode coverage)
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            # Linux - FreeFont (has Devanagari support)
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            # Linux - DejaVu
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # Linux - Liberation
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
            "/Library/Fonts/Kohinoor Devanagari.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            # Windows
            "C:/Windows/Fonts/mangal.ttf",
            "C:/Windows/Fonts/NirmalaUI.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/ArialUni.ttf",
        ]

        for font_path in font_paths:
            if Path(font_path).exists():
                return font_path

        return None

    def _parse_page_markers(self, text: str, num_pages: int) -> list[str]:
        """Parse translated text by page markers.

        Splits text by "--- Page N ---" markers to reconstruct page-by-page content.
        Falls back to even distribution if markers are missing or corrupted.

        Args:
            text: Full translated text potentially containing page markers.
            num_pages: Expected number of pages from source document.

        Returns:
            List of text content for each page.
        """
        import re

        # Pattern to match page markers: "--- Page N ---" with optional whitespace
        pattern = r"---\s*Page\s+(\d+)\s*---"

        # Split by page markers
        parts = re.split(pattern, text)

        # If no markers found, fall back to even distribution
        if len(parts) <= 1:
            # No page markers - distribute text evenly across pages
            lines = text.split("\n")
            lines_per_page = max(1, len(lines) // num_pages)
            page_texts = []
            for i in range(num_pages):
                start = i * lines_per_page
                end = start + lines_per_page if i < num_pages - 1 else len(lines)
                page_texts.append("\n".join(lines[start:end]))
            return page_texts

        # Parse the split result: [text_before, page_num_1, text_1, page_num_2, text_2, ...]
        page_texts = [""] * num_pages

        # First part before any marker (usually empty or whitespace)
        i = 0
        while i < len(parts):
            if i == 0 and not re.match(r"^\d+$", parts[i]):
                # Text before first marker - prepend to page 1
                if parts[i].strip():
                    page_texts[0] = parts[i].strip()
                i += 1
            elif i < len(parts) - 1 and re.match(r"^\d+$", parts[i]):
                # This is a page number, next part is the content
                page_num = int(parts[i])
                if 1 <= page_num <= num_pages and i + 1 < len(parts):
                    content = parts[i + 1].strip()
                    page_texts[page_num - 1] = content
                i += 2
            else:
                i += 1

        return page_texts

    def _calculate_fit_font_size(
        self,
        text: str,
        page_width: float,
        page_height: float,
        margin: float,
        base_font_size: float = 11.0,
        min_font_size: float = 6.0,
    ) -> float:
        """Calculate font size that fits text within page boundaries.

        Args:
            text: Text to fit on the page.
            page_width: Page width in points.
            page_height: Page height in points.
            margin: Margin on all sides.
            base_font_size: Starting font size to try.
            min_font_size: Minimum allowed font size.

        Returns:
            Font size that fits the text, or min_font_size if text is too long.
        """
        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin

        # Start with base font size and scale down if needed
        font_size = base_font_size

        while font_size >= min_font_size:
            # Wrap text at current font size
            lines = self._wrap_text_for_pdf(text, usable_width, font_size)

            # Calculate total height needed (line_height = font_size * 1.4)
            line_height = font_size * 1.4
            total_height = len(lines) * line_height

            if total_height <= usable_height:
                return font_size

            # Scale down by 10%
            font_size *= 0.9

        return min_font_size

    def _add_metadata_to_pdf_page(
        self,
        page: fitz.Page,
        metadata: OutputMetadata,
        margin: float,
        font_size: float,
        font_path: Optional[str] = None,
    ) -> None:
        """Add metadata information to a PDF page.

        Args:
            page: The fitz Page object.
            metadata: Output metadata.
            margin: Page margin in points.
            font_size: Font size for text.
            font_path: Path to font file for Unicode support.
        """
        y_position = margin
        line_height = font_size + 4

        # Title
        self._insert_text_with_font(
            page, margin, y_position,
            "LegacyLipi Translation Output",
            16, font_path, color=(0, 0, 0)
        )
        y_position += line_height * 2

        # Metadata lines
        meta_lines = [
            f"Source File: {metadata.source_file}",
            f"Encoding: {metadata.encoding_detected} (confidence: {metadata.encoding_confidence:.1%})",
            f"Languages: {metadata.source_language} -> {metadata.target_language}",
            f"Translation Backend: {metadata.translation_backend}",
            f"Pages: {metadata.page_count}",
            f"Generated: {metadata.generated_at}",
        ]

        for line in meta_lines:
            self._insert_text_with_font(
                page, margin, y_position,
                line, font_size, font_path, color=(0.3, 0.3, 0.3)
            )
            y_position += line_height

        # Add separator line
        y_position += line_height
        page.draw_line(
            (margin, y_position),
            (page.rect.width - margin, y_position),
            color=(0.7, 0.7, 0.7),
            width=0.5,
        )

    def _wrap_text_for_pdf(
        self,
        text: str,
        max_width: float,
        font_size: float,
        chars_per_line: int = 80,
    ) -> list[str]:
        """Wrap text to fit within a given width.

        Args:
            text: Text to wrap.
            max_width: Maximum width in points.
            font_size: Font size being used.
            chars_per_line: Approximate characters per line.

        Returns:
            List of wrapped lines.
        """
        lines = []

        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue

            # Simple word wrapping
            words = paragraph.split()
            current_line = []
            current_length = 0

            for word in words:
                word_length = len(word)
                if current_length + word_length + 1 <= chars_per_line:
                    current_line.append(word)
                    current_length += word_length + 1
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length

            if current_line:
                lines.append(" ".join(current_line))

        return lines

    def generate(
        self,
        document: PDFDocument,
        encoding_result: EncodingDetectionResult,
        translation_result: Optional[TranslationResult] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
        translated_text: Optional[str] = None,
    ) -> Union[str, bytes]:
        """Generate output in the specified format.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.
            output_format: Desired output format.
            translated_text: Optional translated text to use.

        Returns:
            Formatted output string (for text/markdown) or bytes (for PDF).

        Raises:
            ValueError: If output format is not supported.
        """
        if output_format == OutputFormat.TEXT:
            return self.generate_text(
                document, encoding_result, translation_result, translated_text
            )
        elif output_format == OutputFormat.MARKDOWN:
            return self.generate_markdown(
                document, encoding_result, translation_result, translated_text
            )
        elif output_format == OutputFormat.PDF:
            return self.generate_pdf(
                document, encoding_result, translation_result, translated_text
            )
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save(
        self,
        content: Union[str, bytes],
        output_path: Path,
    ) -> None:
        """Save content to a file.

        Args:
            content: Content to save (str for text/markdown, bytes for PDF).
            output_path: Path to save to.
        """
        if isinstance(content, bytes):
            output_path.write_bytes(content)
        else:
            output_path.write_text(content, encoding="utf-8")


def generate_output(
    document: PDFDocument,
    encoding_result: EncodingDetectionResult,
    translation_result: Optional[TranslationResult] = None,
    output_format: OutputFormat = OutputFormat.TEXT,
) -> str:
    """Convenience function to generate output.

    Args:
        document: The processed PDF document.
        encoding_result: The encoding detection result.
        translation_result: The translation result.
        output_format: Desired output format.

    Returns:
        Formatted output string.
    """
    generator = OutputGenerator()
    return generator.generate(
        document, encoding_result, translation_result, output_format
    )
