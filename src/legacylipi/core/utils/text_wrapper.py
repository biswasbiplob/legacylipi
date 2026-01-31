"""Text wrapping utilities for PDF generation."""

from pathlib import Path
from typing import Optional

try:
    import fitz
except ImportError:
    fitz = None


class TextWrapper:
    """Text wrapping and font sizing utilities for PDF generation."""

    def __init__(self, font_path: Optional[str] = None):
        """Initialize text wrapper.

        Args:
            font_path: Optional path to font file for precise measurements.
        """
        self._font: Optional["fitz.Font"] = None
        if font_path and fitz and Path(font_path).exists():
            try:
                self._font = fitz.Font(fontfile=font_path)
            except Exception:
                pass

    def wrap_to_width_simple(
        self,
        text: str,
        chars_per_line: int = 80,
    ) -> list[str]:
        """Simple word wrapping by character count.

        Args:
            text: Text to wrap.
            chars_per_line: Approximate characters per line.

        Returns:
            List of wrapped lines.
        """
        lines = []

        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue

            words = paragraph.split()
            current_line: list[str] = []
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

    def wrap_to_width_precise(
        self,
        text: str,
        max_width: float,
        font_size: float,
    ) -> list[str]:
        """Wrap text using font metrics for precise measurement.

        Args:
            text: Text to wrap.
            max_width: Maximum width in points.
            font_size: Font size being used.

        Returns:
            List of wrapped lines.
        """
        lines = []

        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append('')
                continue

            words = paragraph.split()
            current_line: list[str] = []
            current_width = 0.0

            for word in words:
                if self._font:
                    word_width = self._font.text_length(word, fontsize=font_size)
                    space_width = self._font.text_length(' ', fontsize=font_size)
                else:
                    # Fallback estimation (average char width ~0.5 * font_size)
                    word_width = len(word) * font_size * 0.5
                    space_width = font_size * 0.25

                test_width = current_width + (space_width if current_line else 0) + word_width

                if test_width <= max_width:
                    current_line.append(word)
                    current_width = test_width
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width

            if current_line:
                lines.append(' '.join(current_line))

        return lines if lines else ['']

    def calculate_fit_font_size(
        self,
        text: str,
        width: float,
        height: float,
        margin: float = 0.0,
        base_font_size: float = 11.0,
        min_font_size: float = 6.0,
    ) -> float:
        """Calculate font size that fits text within page boundaries.

        Args:
            text: Text to fit.
            width: Available width in points.
            height: Available height in points.
            margin: Margin to subtract from dimensions.
            base_font_size: Starting font size to try.
            min_font_size: Minimum allowed font size.

        Returns:
            Font size that fits the text, or min_font_size if text is too long.
        """
        usable_width = width - 2 * margin
        usable_height = height - 2 * margin

        font_size = base_font_size

        while font_size >= min_font_size:
            # Wrap text at current font size
            chars_per_line = int(usable_width / (font_size * 0.5))
            lines = self.wrap_to_width_simple(text, chars_per_line)

            # Calculate total height needed (line_height = font_size * 1.4)
            line_height = font_size * 1.4
            total_height = len(lines) * line_height

            if total_height <= usable_height:
                return font_size

            # Scale down by 10%
            font_size *= 0.9

        return min_font_size

    def calculate_block_font_size(
        self,
        text: str,
        available_width: float,
        available_height: float,
        original_font_size: float,
        min_font_size: float = 5.0,
        max_font_size: float = 12.0,
    ) -> float:
        """Calculate font size that fits text within a bounding box.

        Args:
            text: Text to fit.
            available_width: Width of bounding box in points.
            available_height: Height of bounding box in points.
            original_font_size: Original font size to start with.
            min_font_size: Minimum font size threshold.
            max_font_size: Maximum font size cap for consistency.

        Returns:
            Font size that fits, or min_font_size if text is too long.
        """
        # Cap at max_font_size for consistency across the document
        font_size = max(min_font_size, min(original_font_size, max_font_size))

        while font_size >= min_font_size:
            # Wrap text at current font size
            lines = self.wrap_to_width_precise(text, available_width, font_size)

            # Calculate total height needed (line_height = font_size * 1.2)
            line_height = font_size * 1.2
            total_height = len(lines) * line_height

            if total_height <= available_height:
                return font_size

            font_size *= 0.9  # Scale down by 10%

        return min_font_size
