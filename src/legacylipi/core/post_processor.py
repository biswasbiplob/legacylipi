"""Generic Devanagari post-processing framework.

This module provides a post-processing pipeline for text converted from
legacy encodings to Unicode Devanagari. It handles common issues like
matra ordering, nukta placement, visarga/anusvara ordering, and
whitespace normalization.

Each encoding can have its own specialized post-processor, while a
common post-processor handles issues shared across all Devanagari encodings.
"""

import re
from abc import ABC, abstractmethod


class DevanagariPostProcessor(ABC):
    """Base class for encoding-specific post-processors."""

    @abstractmethod
    def process(self, text: str) -> str:
        """Apply post-processing rules to converted text.

        Args:
            text: Text after initial character mapping from legacy to Unicode.

        Returns:
            Text with corrected Unicode ordering and normalization.
        """
        pass


class CommonDevanagariPostProcessor(DevanagariPostProcessor):
    """Common post-processing rules applicable to all Devanagari encodings.

    Handles issues that are universal across legacy encoding conversions:
    - Matra ordering (e.g., ा + े -> ो)
    - Nukta placement after base consonant
    - Visarga/anusvara ordering after matras
    - Whitespace normalization around combining marks
    """

    def process(self, text: str) -> str:
        """Apply common Devanagari post-processing rules.

        Args:
            text: Text after initial character mapping.

        Returns:
            Text with corrected Unicode ordering.
        """
        text = self._fix_matra_ordering(text)
        text = self._fix_nukta_placement(text)
        text = self._fix_visarga_ordering(text)
        text = self._normalize_whitespace(text)
        return text

    def _fix_matra_ordering(self, text: str) -> str:
        """Fix common matra ordering issues.

        Some legacy encodings produce matras in the wrong order when
        converting to Unicode. This fixes the most common cases.
        """
        # ा + े -> ो
        text = text.replace("\u093e\u0947", "\u094b")
        # ा + ै -> ौ
        text = text.replace("\u093e\u0948", "\u094c")
        # े + ा -> ो
        text = text.replace("\u0947\u093e", "\u094b")
        # ै + ा -> ौ
        text = text.replace("\u0948\u093e", "\u094c")
        return text

    def _fix_nukta_placement(self, text: str) -> str:
        """Ensure nukta comes right after base consonant.

        In Unicode, nukta (़) should appear between the consonant and
        any following matra, not after the matra.
        """
        # Nukta should be between consonant and matra
        consonants = "[\u0915-\u0939\u0958-\u095f]"
        matras = "[\u093e-\u094c\u0962\u0963]"
        text = re.sub(
            f"({consonants})({matras})(\u093c)",
            r"\1\3\2",
            text,
        )
        return text

    def _fix_visarga_ordering(self, text: str) -> str:
        """Ensure visarga/anusvara come after matras.

        Visarga (ः), anusvara (ं), and chandrabindu (ँ) should appear
        after any vowel matras, not before them.
        """
        text = re.sub(
            r"([\u0903\u0902\u0901])([\u093e-\u094c]+)",
            r"\2\1",
            text,
        )
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Clean up space + matra issues.

        Combining marks (matras, halant, anusvara, etc.) should attach
        to the previous character, not be separated by whitespace.
        """
        text = re.sub(
            r"(\s+)([\u094d\u093e-\u094c\u0902\u0901])",
            r"\2",
            text,
        )
        return text


class ShreeDevPostProcessor(DevanagariPostProcessor):
    """Post-processor for SHREE-DEV encoding.

    Wraps the existing apply_shree_dev_post_processing function from
    the shree_dev mapping module, which handles SHREE-DEV specific
    issues like placeholder reordering for इ matra and र् (repha).
    """

    def process(self, text: str) -> str:
        """Apply SHREE-DEV specific post-processing.

        Args:
            text: Text after initial SHREE-DEV character mapping.

        Returns:
            Text with SHREE-DEV specific corrections applied.
        """
        from legacylipi.mappings.shree_dev import apply_shree_dev_post_processing

        return apply_shree_dev_post_processing(text)


# Registry of post-processors for specific encodings
POST_PROCESSORS: dict[str, DevanagariPostProcessor] = {
    "shree-dev": ShreeDevPostProcessor(),
    "shree-dev-0714": ShreeDevPostProcessor(),
    "shree-dev-0708": ShreeDevPostProcessor(),
}

# Default post-processor for all other Devanagari encodings
_common_processor = CommonDevanagariPostProcessor()


def get_post_processor(encoding_name: str) -> DevanagariPostProcessor:
    """Get the post-processor for an encoding.

    Returns the encoding-specific post-processor if one is registered,
    otherwise returns the common Devanagari post-processor.

    Args:
        encoding_name: Name of the encoding (case-insensitive).

    Returns:
        DevanagariPostProcessor instance for the given encoding.
    """
    return POST_PROCESSORS.get(encoding_name.lower(), _common_processor)
