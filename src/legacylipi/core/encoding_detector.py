"""Encoding Detection module for identifying legacy font encodings.

This module provides functionality to detect whether text is Unicode or
uses a legacy Indian font encoding (Shree-Lipi, Kruti Dev, etc.).
"""

import re
from dataclasses import dataclass
from typing import Optional

from legacylipi.core.models import (
    DetectionMethod,
    EncodingDetectionResult,
    FontInfo,
    PDFDocument,
    TextBlock,
)


# Unicode ranges for Indian scripts
DEVANAGARI_RANGE = (0x0900, 0x097F)
DEVANAGARI_EXTENDED_RANGE = (0xA8E0, 0xA8FF)
VEDIC_EXTENSIONS_RANGE = (0x1CD0, 0x1CFF)


@dataclass
class LegacyFontPattern:
    """Pattern for matching legacy font names."""

    encoding_name: str
    patterns: list[str]  # Regex patterns
    signatures: list[str]  # Text signatures for heuristic detection
    priority: int = 0  # Higher priority = checked first


# Known Unicode Devanagari fonts (should not be converted)
UNICODE_FONT_PATTERNS = [
    r"sakal[-_\s]*marathi",
    r"mangal",
    r"nirmala[-_\s]*ui",
    r"aparajita",
    r"kokila",
    r"utsaah",
    r"shruti",
    r"lohit[-_\s]*devanagari",
    r"noto[-_\s]*sans[-_\s]*devanagari",
    r"adobe[-_\s]*devanagari",
    r"tiro[-_\s]*devanagari",
    r"poppins[-_\s]*devanagari",
]

# Database of known legacy font patterns
LEGACY_FONT_PATTERNS: list[LegacyFontPattern] = [
    LegacyFontPattern(
        encoding_name="shree-lipi",
        patterns=[
            r"shree[-_\s]*dev[-_\s]*07\d{2}",
            r"shree[-_\s]*lipi",
            r"shree[-_\s]*dev",
            r"sdl[-_\s]*dev",
        ],
        signatures=["´Ö", "Æü", "Ö¸ü", "®Ö", "ÖμÖ", "ÖÂ", "™Òü", "×", "†"],
        priority=9,
    ),
    LegacyFontPattern(
        encoding_name="kruti-dev",
        patterns=[
            r"kruti[-_\s]*dev",
            r"krutidev",
            r"kruti[-_\s]*\d+",
        ],
        signatures=["d`fr", "Hkkjr", "ns'k", "gS", "fd", "dh", "esa", "ls"],
        priority=9,
    ),
    LegacyFontPattern(
        encoding_name="aps-dv",
        patterns=[
            r"aps[-_\s]*dv",
            r"aps[-_\s]*c[-_\s]*dv",
        ],
        signatures=["¼ã", "ãä", "äã", "Úæ"],
        priority=8,
    ),
    LegacyFontPattern(
        encoding_name="chanakya",
        patterns=[
            r"chanakya",
            r"chankya",
        ],
        signatures=["Ñfr", "Ákns'k", "Hkkjr"],
        priority=7,
    ),
    LegacyFontPattern(
        encoding_name="walkman-chanakya",
        patterns=[
            r"walkman[-_\s]*chanakya",
            r"wm[-_\s]*chanakya",
        ],
        signatures=["Ökfr", "çns'k"],
        priority=8,
    ),
    LegacyFontPattern(
        encoding_name="dvb-tt",
        patterns=[
            r"dvb[-_\s]*tt",
            r"dv[-_\s]*tt[-_\s]*yogesh",
            r"dvbw[-_\s]*tt",
            r"dvbwtt[-_\s]*surekh",
            r"dvbtt[-_\s]*surekh",
            r"surekh[-_\s]*(normal|bold)",
        ],
        # Signatures for DVB-TT font - common patterns found in text
        signatures=["´Ö", "¿Ö", "Ã", "®", "×¾Ö", "×¬Ö", "¸ü", "Æü", "ÖÓ", "†×"],
        priority=10,  # Higher priority - common in Marathi govt docs
    ),
    LegacyFontPattern(
        encoding_name="shusha",
        patterns=[
            r"shusha",
            r"shushaa",
        ],
        signatures=["ÉÉ®úiÉ", "½þè"],
        priority=6,
    ),
    LegacyFontPattern(
        encoding_name="agra",
        patterns=[
            r"agra[-_\s]*\d*",
        ],
        signatures=[],
        priority=5,
    ),
    LegacyFontPattern(
        encoding_name="akruti",
        patterns=[
            r"akruti",
            r"aku[-_\s]*dev",
        ],
        signatures=[],
        priority=5,
    ),
]


class EncodingDetector:
    """Detector for identifying font encodings in PDF documents."""

    def __init__(self, custom_patterns: Optional[list[LegacyFontPattern]] = None):
        """Initialize the encoding detector.

        Args:
            custom_patterns: Additional font patterns to use for detection.
        """
        self.patterns = list(LEGACY_FONT_PATTERNS)
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        # Sort by priority (descending)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)

        # Compile regex patterns for efficiency
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for pattern in self.patterns:
            self._compiled_patterns[pattern.encoding_name] = [
                re.compile(p, re.IGNORECASE) for p in pattern.patterns
            ]

        # Compile Unicode font patterns
        self._unicode_patterns = [
            re.compile(p, re.IGNORECASE) for p in UNICODE_FONT_PATTERNS
        ]

    def detect_from_font_name(self, font_name: str) -> Optional[EncodingDetectionResult]:
        """Detect encoding from a font name.

        Args:
            font_name: The font name to check.

        Returns:
            EncodingDetectionResult if a legacy encoding is detected, None otherwise.
        """
        if not font_name:
            return None

        font_lower = font_name.lower()

        # First check if this is a known Unicode Devanagari font
        for unicode_pattern in self._unicode_patterns:
            if unicode_pattern.search(font_lower):
                return EncodingDetectionResult(
                    detected_encoding="unicode-devanagari",
                    confidence=1.0,
                    method=DetectionMethod.UNICODE_DETECTED,
                    font_name=font_name,
                )

        # Then check for legacy encodings
        for pattern in self.patterns:
            for compiled in self._compiled_patterns[pattern.encoding_name]:
                if compiled.search(font_lower):
                    return EncodingDetectionResult(
                        detected_encoding=pattern.encoding_name,
                        confidence=0.95,
                        method=DetectionMethod.FONT_MATCH,
                        font_name=font_name,
                    )

        return None

    def detect_unicode(self, text: str) -> bool:
        """Check if text contains Unicode Devanagari characters.

        Args:
            text: The text to check.

        Returns:
            True if the text contains Devanagari Unicode characters.
        """
        if not text:
            return False

        devanagari_count = 0
        for char in text:
            code_point = ord(char)
            if (
                DEVANAGARI_RANGE[0] <= code_point <= DEVANAGARI_RANGE[1]
                or DEVANAGARI_EXTENDED_RANGE[0] <= code_point <= DEVANAGARI_EXTENDED_RANGE[1]
                or VEDIC_EXTENSIONS_RANGE[0] <= code_point <= VEDIC_EXTENSIONS_RANGE[1]
            ):
                devanagari_count += 1

        # If more than 10% of non-whitespace chars are Devanagari, it's Unicode
        non_whitespace = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        if non_whitespace > 0:
            return devanagari_count / non_whitespace > 0.1

        return False

    def detect_from_text_heuristic(self, text: str) -> EncodingDetectionResult:
        """Detect encoding using heuristic text analysis.

        This is used when font metadata is unavailable or inconclusive.

        Args:
            text: The text to analyze.

        Returns:
            EncodingDetectionResult with detected encoding and confidence.
        """
        if not text:
            return EncodingDetectionResult(
                detected_encoding="unknown",
                confidence=0.0,
                method=DetectionMethod.HEURISTIC,
            )

        # First check if it's already Unicode
        if self.detect_unicode(text):
            return EncodingDetectionResult(
                detected_encoding="unicode-devanagari",
                confidence=1.0,
                method=DetectionMethod.UNICODE_DETECTED,
            )

        # Check for legacy font signatures
        best_match: Optional[str] = None
        best_score = 0
        fallbacks: list[str] = []

        for pattern in self.patterns:
            if not pattern.signatures:
                continue

            matches = sum(1 for sig in pattern.signatures if sig in text)
            if matches > 0:
                # Score based on number of matching signatures
                score = matches / len(pattern.signatures)
                if score > best_score:
                    if best_match:
                        fallbacks.append(best_match)
                    best_match = pattern.encoding_name
                    best_score = score
                elif score > 0.3:  # Potential fallback
                    fallbacks.append(pattern.encoding_name)

        if best_match and best_score >= 0.3:
            # Calculate confidence based on score
            confidence = min(0.90, 0.60 + (best_score * 0.30))
            return EncodingDetectionResult(
                detected_encoding=best_match,
                confidence=confidence,
                method=DetectionMethod.HEURISTIC,
                fallback_encodings=fallbacks[:3],  # Top 3 fallbacks
            )

        # Check for general legacy encoding indicators
        # Legacy encodings often have high concentration of extended ASCII
        extended_ascii_count = sum(1 for c in text if 128 <= ord(c) <= 255)
        total_chars = len(text)

        if total_chars > 0 and extended_ascii_count / total_chars > 0.2:
            return EncodingDetectionResult(
                detected_encoding="unknown-legacy",
                confidence=0.50,
                method=DetectionMethod.HEURISTIC,
                fallback_encodings=["shree-lipi", "kruti-dev"],
            )

        return EncodingDetectionResult(
            detected_encoding="unknown",
            confidence=0.0,
            method=DetectionMethod.HEURISTIC,
        )

    def detect_from_fonts(self, fonts: list[FontInfo]) -> Optional[EncodingDetectionResult]:
        """Detect encoding from a list of fonts.

        Args:
            fonts: List of FontInfo objects.

        Returns:
            EncodingDetectionResult if legacy encoding detected, None otherwise.
        """
        for font in fonts:
            result = self.detect_from_font_name(font.name)
            if result:
                return result
        return None

    def detect_from_text_block(self, block: TextBlock) -> EncodingDetectionResult:
        """Detect encoding for a single text block.

        Uses both font name (if available) and text content for detection.

        Args:
            block: The TextBlock to analyze.

        Returns:
            EncodingDetectionResult with detected encoding.
        """
        # Try font name first (highest confidence)
        if block.font_name:
            result = self.detect_from_font_name(block.font_name)
            if result:
                return result

        # Fall back to heuristic detection
        return self.detect_from_text_heuristic(block.raw_text)

    def detect_from_document(
        self, document: PDFDocument
    ) -> tuple[EncodingDetectionResult, dict[int, EncodingDetectionResult]]:
        """Detect encoding for an entire document.

        Returns both a document-level detection and per-page results.

        Args:
            document: The PDFDocument to analyze.

        Returns:
            Tuple of (overall_result, {page_number: result}).
        """
        page_results: dict[int, EncodingDetectionResult] = {}
        encoding_counts: dict[str, int] = {}
        total_confidence = 0.0
        result_count = 0

        # First try document-level font detection
        if document.fonts:
            doc_font_result = self.detect_from_fonts(document.fonts)
            if doc_font_result and doc_font_result.is_legacy:
                # High confidence from document fonts
                for page in document.pages:
                    page_results[page.page_number] = doc_font_result
                return doc_font_result, page_results

        # Analyze each page
        for page in document.pages:
            page_encoding: Optional[str] = None
            page_confidence = 0.0
            page_method = DetectionMethod.HEURISTIC

            # Check fonts on this page
            for block in page.text_blocks:
                result = self.detect_from_text_block(block)

                if result.confidence > page_confidence:
                    page_encoding = result.detected_encoding
                    page_confidence = result.confidence
                    page_method = result.method

            if page_encoding:
                page_result = EncodingDetectionResult(
                    detected_encoding=page_encoding,
                    confidence=page_confidence,
                    method=page_method,
                )
                page_results[page.page_number] = page_result

                # Track for overall statistics
                encoding_counts[page_encoding] = encoding_counts.get(page_encoding, 0) + 1
                total_confidence += page_confidence
                result_count += 1

        # Determine overall document encoding
        if not encoding_counts:
            return (
                EncodingDetectionResult(
                    detected_encoding="unknown",
                    confidence=0.0,
                    method=DetectionMethod.HEURISTIC,
                ),
                page_results,
            )

        # Find most common encoding
        most_common = max(encoding_counts.items(), key=lambda x: x[1])
        overall_encoding = most_common[0]
        avg_confidence = total_confidence / result_count if result_count > 0 else 0.0

        # Determine overall method
        overall_method = DetectionMethod.HEURISTIC
        for result in page_results.values():
            if result.detected_encoding == overall_encoding:
                overall_method = result.method
                break

        overall_result = EncodingDetectionResult(
            detected_encoding=overall_encoding,
            confidence=avg_confidence,
            method=overall_method,
            fallback_encodings=[
                enc for enc, _ in sorted(encoding_counts.items(), key=lambda x: -x[1])[1:4]
            ],
        )

        return overall_result, page_results


def detect_encoding(
    text: Optional[str] = None,
    font_name: Optional[str] = None,
    document: Optional[PDFDocument] = None,
) -> EncodingDetectionResult:
    """Convenience function for encoding detection.

    Args:
        text: Text to analyze (for heuristic detection).
        font_name: Font name to check.
        document: Full PDF document to analyze.

    Returns:
        EncodingDetectionResult with detected encoding.
    """
    detector = EncodingDetector()

    if document:
        result, _ = detector.detect_from_document(document)
        return result

    if font_name:
        result = detector.detect_from_font_name(font_name)
        if result:
            return result

    if text:
        return detector.detect_from_text_heuristic(text)

    return EncodingDetectionResult(
        detected_encoding="unknown",
        confidence=0.0,
        method=DetectionMethod.HEURISTIC,
    )
