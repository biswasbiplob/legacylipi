"""Output Generator module for creating translated document outputs.

This module handles generating various output formats from translated content,
including plain text, Markdown, PDF, and side-by-side bilingual documents.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import fitz  # PyMuPDF

from legacylipi.core.font_analyzer import FontSizeAnalyzer
from legacylipi.core.models import (
    EncodingDetectionResult,
    OutputFormat,
    PDFDocument,
    TextBlock,
    TranslationResult,
)
from legacylipi.core.utils.text_wrapper import TextWrapper


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
        self._text_wrapper: TextWrapper | None = None  # Lazy initialized with font

    def _get_text_wrapper(self, font_path: str | None = None) -> TextWrapper:
        """Get or create TextWrapper with font support."""
        if self._text_wrapper is None or font_path:
            self._text_wrapper = TextWrapper(font_path)
        return self._text_wrapper

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
        structure_preserving_translation: bool = False,
    ) -> bytes:
        """Generate PDF output preserving document structure.

        Args:
            document: The processed PDF document.
            encoding_result: The encoding detection result.
            translation_result: The translation result.
            translated_text: Translated text to use (overrides translation_result).
            output_path: Optional path to save PDF directly.
            preserve_structure: If True, preserve original page dimensions and text positions.
            structure_preserving_translation: If True, use block-level translation with
                position preservation (blocks must have translated_text populated).

        Returns:
            PDF content as bytes.
        """
        # Create a new PDF document
        pdf_doc = fitz.open()

        # Get metadata for header
        metadata = self.generate_metadata(document, encoding_result, translation_result)

        # Find a font that supports the content
        font_path = self._get_unicode_font()

        # Check for structure-preserving translation mode
        if structure_preserving_translation:
            # Check if we have translated blocks with positions
            has_translated_blocks = any(
                block.translated_text is not None
                for page in document.pages
                for block in page.text_blocks
                if block.position is not None
            )
            if has_translated_blocks:
                return self._generate_pdf_structure_preserving_translation(
                    pdf_doc, document, metadata, output_path, font_path
                )

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

    def _calculate_block_font_size(
        self,
        text: str,
        available_width: float,
        available_height: float,
        original_font_size: float,
        min_font_size: float = 5.0,
        max_font_size: float = 12.0,
        font_path: Optional[str] = None,
    ) -> float:
        """Calculate font size that fits text within a bounding box.

        Strategy:
        1. Start with the smaller of original font size or max_font_size
        2. If text doesn't fit, scale down by 10% increments
        3. Stop at min_font_size

        Args:
            text: Text to fit.
            available_width: Width of bounding box in points.
            available_height: Height of bounding box in points.
            original_font_size: Original font size to start with.
            min_font_size: Minimum font size threshold.
            max_font_size: Maximum font size cap for consistency.
            font_path: Path to font file for measurement.

        Returns:
            Font size that fits, or min_font_size if text is too long.
        """
        wrapper = self._get_text_wrapper(font_path)
        return wrapper.calculate_block_font_size(
            text, available_width, available_height,
            original_font_size, min_font_size, max_font_size
        )

    def _wrap_text_to_width_precise(
        self,
        text: str,
        max_width: float,
        font_size: float,
        font: Optional[fitz.Font] = None,
    ) -> list[str]:
        """Wrap text using font metrics for precise measurement.

        Args:
            text: Text to wrap.
            max_width: Maximum width in points.
            font_size: Font size being used.
            font: fitz.Font object for measurement (optional).

        Returns:
            List of wrapped lines.
        """
        # Use TextWrapper's precise wrapping
        wrapper = self._get_text_wrapper()
        return wrapper.wrap_to_width_precise(text, max_width, font_size)

    def _preprocess_overlapping_blocks(
        self,
        blocks: list,
        gap: float = 4.0,
    ) -> list:
        """Detect and resolve overlapping bounding boxes before rendering.

        OCR can produce blocks with overlapping or touching bounding boxes.
        This pre-processing step detects such overlaps and adjusts block
        positions to prevent text from overlapping in the output.

        Args:
            blocks: List of (TextBlock, text) tuples with position data.
            gap: Minimum gap to maintain between blocks.

        Returns:
            List of (TextBlock, text) tuples with adjusted positions.
        """
        if not blocks:
            return blocks

        # Create mutable copies of position data for adjustment
        # We'll track adjusted y0 values separately to avoid modifying originals
        adjusted_blocks = []
        for block, text in blocks:
            # Store original bbox and create adjustment info
            bbox = block.position
            adjusted_blocks.append({
                'block': block,
                'text': text,
                'orig_y0': bbox.y0,
                'orig_y1': bbox.y1,
                'adj_y0': bbox.y0,  # Will be adjusted if overlap detected
                'x0': bbox.x0,
                'x1': bbox.x1,
            })

        # Sort by y0 first, then x0 (top-to-bottom, left-to-right)
        adjusted_blocks.sort(key=lambda b: (b['orig_y0'], b['x0']))

        # Track occupied regions: list of (y_end, x0, x1)
        occupied = []

        for i, item in enumerate(adjusted_blocks):
            # Check for overlap with all previously processed blocks
            intended_y0 = item['orig_y0']
            min_y0 = intended_y0

            for (occ_y_end, occ_x0, occ_x1) in occupied:
                # Check horizontal overlap
                if not (item['x1'] < occ_x0 or item['x0'] > occ_x1):
                    # Horizontal overlap exists
                    # Check if current block starts before occupied region ends
                    if intended_y0 < occ_y_end + gap:
                        # Overlap detected - push down
                        if occ_y_end + gap > min_y0:
                            min_y0 = occ_y_end + gap

            # Apply adjustment
            item['adj_y0'] = min_y0

            # Calculate adjusted y1 (maintain original height)
            height = item['orig_y1'] - item['orig_y0']
            adj_y1 = min_y0 + height

            # Record this block's occupied region
            occupied.append((adj_y1, item['x0'], item['x1']))

        # Return adjusted blocks with modified position info
        # We need to create new BoundingBox objects with adjusted y values
        from legacylipi.core.models import BoundingBox

        result = []
        for item in adjusted_blocks:
            block = item['block']
            text = item['text']

            # If position was adjusted, create a modified block
            if item['adj_y0'] != item['orig_y0']:
                # Create adjusted bounding box
                height = item['orig_y1'] - item['orig_y0']
                adjusted_bbox = BoundingBox(
                    x0=block.position.x0,
                    y0=item['adj_y0'],
                    x1=block.position.x1,
                    y1=item['adj_y0'] + height,
                )
                # Create a copy of the block with adjusted position
                # We use dataclasses.replace if available, otherwise manual copy
                from dataclasses import replace
                adjusted_block = replace(block, position=adjusted_bbox)
                result.append((adjusted_block, text))
            else:
                result.append((block, text))

        return result

    def _place_translated_blocks_with_positions(
        self,
        page: fitz.Page,
        text_blocks: list,
        font_path: Optional[str],
        min_font_size: float = 5.0,
        padding: float = 2.0,
        font_analyzer: Optional[FontSizeAnalyzer] = None,
    ) -> None:
        """Place translated text blocks at original positions with font scaling.

        For structure-preserving translation: places translated text at original
        positions, scaling font size to fit within original bounding boxes.
        Includes collision detection to prevent overlapping text.

        Args:
            page: The fitz page to write to.
            text_blocks: List of TextBlock objects with position and translated_text.
            font_path: Path to Unicode font.
            min_font_size: Minimum font size threshold (don't go below this).
            padding: Padding inside bounding box.
            font_analyzer: Pre-analyzed FontSizeAnalyzer for normalized sizes.
        """
        # Constants for edge cases
        min_block_width = 20
        min_block_height = 10
        vertical_gap = 8  # Minimum gap between blocks

        # Load font once for reuse
        font = None
        if font_path and Path(font_path).exists():
            try:
                font = fitz.Font(fontfile=font_path)
            except Exception:
                pass

        # Filter valid blocks
        valid_blocks = []
        for block in text_blocks:
            text = block.translated_text or block.unicode_text or block.raw_text
            if not text or not text.strip():
                continue
            if not block.position:
                continue
            bbox = block.position
            if bbox.width < min_block_width or bbox.height < min_block_height:
                continue
            valid_blocks.append((block, text))

        # Pre-process blocks to detect and resolve overlapping source bboxes
        # This handles the case where OCR produces overlapping bounding boxes
        valid_blocks = self._preprocess_overlapping_blocks(valid_blocks, gap=vertical_gap)

        # Track occupied vertical regions per column (approximate column detection)
        # Format: list of (y_end, x0, x1) tuples representing rendered regions
        occupied_regions: list[tuple[float, float, float]] = []

        for block, text in valid_blocks:
            bbox = block.position

            # Calculate available space (with padding)
            available_width = bbox.width - (2 * padding)
            available_height = bbox.height - (2 * padding)

            if available_width <= 0 or available_height <= 0:
                continue

            # Use FIXED font size for consistency across the document
            # Don't scale down to fit bounding boxes - let text overflow if needed
            # This ensures uniform appearance regardless of OCR bbox variations
            font_size = FontSizeAnalyzer.UNIFORM_SIZE  # Always use 11pt

            # Wrap text to fit width
            wrapped_lines = self._wrap_text_to_width_precise(
                text=text,
                max_width=available_width,
                font_size=font_size,
                font=font,
            )

            line_height = font_size * 1.2
            total_text_height = len(wrapped_lines) * line_height

            # Calculate starting Y position, checking for collisions
            intended_y_start = bbox.y0 + padding

            # Find the lowest occupied region that overlaps horizontally with this block
            min_y_start = intended_y_start
            for (occupied_y_end, occupied_x0, occupied_x1) in occupied_regions:
                # Check if there's horizontal overlap
                if not (bbox.x1 < occupied_x0 or bbox.x0 > occupied_x1):
                    # Horizontal overlap exists - ensure we start below this region
                    if occupied_y_end + vertical_gap > min_y_start:
                        min_y_start = occupied_y_end + vertical_gap

            # Use the adjusted Y position (may be pushed down to avoid overlap)
            y_start = max(intended_y_start, min_y_start)

            # Position: top-left of bbox + padding + font baseline offset
            x = bbox.x0 + padding
            y = y_start + font_size  # Add font_size for baseline

            # Render each line
            lines_rendered = 0
            final_y = y  # Track actual final y position after rendering
            for line in wrapped_lines:
                # Allow text to extend somewhat beyond original bbox if needed
                # to avoid truncation, but stop at page boundary
                page_height = page.rect.height
                if y > page_height - padding:
                    break

                self._insert_text_with_font(
                    page, x, y, line.strip(),
                    font_size, font_path
                )
                y += line_height
                final_y = y  # Update to track where we actually ended
                lines_rendered += 1

            # Record the occupied region using actual final y position
            # This ensures collision detection uses the real rendered bounds
            if lines_rendered > 0:
                # final_y is the position where the NEXT line would start
                # which is effectively the bottom of the rendered region
                occupied_regions.append((final_y, bbox.x0, bbox.x1))

    def _generate_pdf_structure_preserving_translation(
        self,
        pdf_doc: fitz.Document,
        document: PDFDocument,
        metadata: OutputMetadata,
        output_path: Optional[Path],
        font_path: Optional[str],
    ) -> bytes:
        """Generate PDF with translated text at original block positions.

        This method creates a PDF where each translated text block is placed
        at its original position with font scaling to fit within bounds.
        Uses FontSizeAnalyzer to normalize font sizes across the document
        while preserving heading/body/caption hierarchy.

        Args:
            pdf_doc: The fitz document to write to.
            document: The processed PDF document with translated blocks.
            metadata: Output metadata.
            output_path: Optional path to save PDF.
            font_path: Path to Unicode font.

        Returns:
            PDF content as bytes.
        """
        # Collect all blocks from all pages for document-wide font analysis
        all_blocks = []
        for page_data in document.pages:
            all_blocks.extend([b for b in page_data.text_blocks if b.position])

        # Analyze font sizes across the entire document
        font_analyzer = FontSizeAnalyzer()
        font_analyzer.analyze_blocks(all_blocks)

        # Set font categories on blocks for reference
        font_analyzer.set_block_categories(all_blocks)

        # Add metadata page if enabled
        if self._include_metadata and document.pages:
            first_page = document.pages[0]
            page_width = first_page.width if first_page.width > 0 else 595
            page_height = first_page.height if first_page.height > 0 else 842
            meta_page = pdf_doc.new_page(width=page_width, height=page_height)
            margin = min(50, page_width * 0.08)
            self._add_metadata_to_pdf_page(meta_page, metadata, margin, 11, font_path)

        # Process each page
        for page_data in document.pages:
            # Use original page dimensions
            page_width = page_data.width if page_data.width > 0 else 595
            page_height = page_data.height if page_data.height > 0 else 842

            # Create new page with original dimensions
            new_page = pdf_doc.new_page(width=page_width, height=page_height)

            # Get positioned blocks (those with bounding box data)
            positioned_blocks = [b for b in page_data.text_blocks if b.position]

            if positioned_blocks:
                self._place_translated_blocks_with_positions(
                    new_page, positioned_blocks, font_path,
                    font_analyzer=font_analyzer
                )
            else:
                # Fallback: render as flowing text if no position data
                margin = 50
                y = margin
                for block in page_data.text_blocks:
                    text = block.translated_text or block.unicode_text or block.raw_text
                    if text:
                        self._insert_text_with_font(
                            new_page, margin, y, text.strip(), 11, font_path
                        )
                        y += 16

        pdf_bytes = pdf_doc.tobytes()

        if output_path:
            pdf_doc.save(output_path)

        pdf_doc.close()
        return pdf_bytes

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
        wrapper = self._get_text_wrapper()
        return wrapper.calculate_fit_font_size(
            text, page_width, page_height, margin, base_font_size, min_font_size
        )

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
        wrapper = self._get_text_wrapper()
        return wrapper.wrap_to_width_simple(text, chars_per_line)

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
