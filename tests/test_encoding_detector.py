"""Tests for Encoding Detector module."""

from pathlib import Path

from legacylipi.core.encoding_detector import (
    LEGACY_FONT_PATTERNS,
    EncodingDetector,
    LegacyFontPattern,
    detect_encoding,
)
from legacylipi.core.models import (
    DetectionMethod,
    EncodingDetectionResult,
    FontInfo,
    PDFDocument,
    PDFPage,
    TextBlock,
)


class TestEncodingDetectorInit:
    """Tests for EncodingDetector initialization."""

    def test_default_initialization(self):
        """Test default initialization with built-in patterns."""
        detector = EncodingDetector()
        assert len(detector.patterns) >= len(LEGACY_FONT_PATTERNS)

    def test_custom_patterns(self):
        """Test initialization with custom patterns."""
        custom = LegacyFontPattern(
            encoding_name="custom-font",
            patterns=[r"my[-_]custom[-_]font"],
            signatures=["ABC"],
            priority=100,
        )
        detector = EncodingDetector(custom_patterns=[custom])
        # Custom pattern should be first (highest priority)
        assert detector.patterns[0].encoding_name == "custom-font"

    def test_patterns_sorted_by_priority(self):
        """Test that patterns are sorted by priority."""
        detector = EncodingDetector()
        priorities = [p.priority for p in detector.patterns]
        assert priorities == sorted(priorities, reverse=True)


class TestFontNameDetection:
    """Tests for font name-based detection."""

    def test_detect_shree_dev_variants(self):
        """Test detection of various Shree-Dev font names."""
        detector = EncodingDetector()

        test_fonts = [
            "Shree-Dev-0714",
            "ShreeDev0714",
            "SHREE_DEV_0702",
            "shree dev 0705",
        ]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "shree-dev"
            assert result.confidence >= 0.9
            assert result.method == DetectionMethod.FONT_MATCH

    def test_detect_shree_lipi_variants(self):
        """Test detection of various Shree-Lipi font names."""
        detector = EncodingDetector()

        test_fonts = [
            "Shree-Lipi",
            "SDL-Dev",
        ]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "shree-lipi"
            assert result.confidence >= 0.9
            assert result.method == DetectionMethod.FONT_MATCH

    def test_detect_kruti_dev(self):
        """Test detection of Kruti Dev fonts."""
        detector = EncodingDetector()

        test_fonts = [
            "KrutiDev",
            "Kruti-Dev",
            "KRUTI_DEV",
            "Kruti Dev 010",
            "krutidev040",
        ]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "kruti-dev"

    def test_detect_aps_dv(self):
        """Test detection of APS-DV fonts."""
        detector = EncodingDetector()

        test_fonts = ["APS-DV", "aps-c-dv", "APS_DV"]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "aps-dv"

    def test_detect_chanakya(self):
        """Test detection of Chanakya fonts."""
        detector = EncodingDetector()

        result = detector.detect_from_font_name("Chanakya")
        assert result is not None
        assert result.detected_encoding == "chanakya"

    def test_detect_walkman_chanakya(self):
        """Test detection of Walkman Chanakya fonts."""
        detector = EncodingDetector()

        test_fonts = ["Walkman-Chanakya", "WM_Chanakya"]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "walkman-chanakya"

    def test_detect_dvb_tt(self):
        """Test detection of DVB-TT fonts."""
        detector = EncodingDetector()

        test_fonts = ["DVB-TT", "DV-TT-Yogesh", "DVBW-TT"]

        for font_name in test_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Failed to detect: {font_name}"
            assert result.detected_encoding == "dvb-tt"

    def test_detect_shusha(self):
        """Test detection of Shusha fonts."""
        detector = EncodingDetector()

        result = detector.detect_from_font_name("Shusha")
        assert result is not None
        assert result.detected_encoding == "shusha"

    def test_standard_fonts_not_detected(self):
        """Test that standard fonts are not falsely detected."""
        detector = EncodingDetector()

        standard_fonts = [
            "Arial",
            "Times New Roman",
            "Helvetica",
        ]

        for font_name in standard_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is None, f"Falsely detected {font_name} as legacy"

    def test_unicode_fonts_detected_as_unicode(self):
        """Test that known Unicode Devanagari fonts are detected as unicode."""
        detector = EncodingDetector()

        unicode_fonts = [
            "Mangal",  # Unicode Hindi font
            "Nirmala UI",
            "Kokila",
            "Sakal Marathi",
        ]

        for font_name in unicode_fonts:
            result = detector.detect_from_font_name(font_name)
            assert result is not None, f"Should detect {font_name}"
            assert result.detected_encoding == "unicode-devanagari", (
                f"Should detect {font_name} as Unicode"
            )
            assert result.is_unicode is True

    def test_empty_font_name(self):
        """Test handling of empty font name."""
        detector = EncodingDetector()

        result = detector.detect_from_font_name("")
        assert result is None

        result = detector.detect_from_font_name(None)
        assert result is None


class TestUnicodeDetection:
    """Tests for Unicode detection."""

    def test_detect_unicode_devanagari(self):
        """Test detection of Unicode Devanagari text."""
        detector = EncodingDetector()

        unicode_texts = [
            "महाराष्ट्र",
            "भारत गणराज्य",
            "हिंदी भाषा",
            "यह एक परीक्षण है",
        ]

        for text in unicode_texts:
            assert detector.detect_unicode(text) is True, f"Failed for: {text}"

    def test_detect_mixed_unicode(self):
        """Test detection of mixed Unicode and ASCII text."""
        detector = EncodingDetector()

        mixed_texts = [
            "Hello महाराष्ट्र World",
            "Test: भारत",
            "2024 में हिंदी",
        ]

        for text in mixed_texts:
            assert detector.detect_unicode(text) is True, f"Failed for: {text}"

    def test_ascii_not_detected_as_unicode(self):
        """Test that pure ASCII is not detected as Unicode."""
        detector = EncodingDetector()

        ascii_texts = [
            "Hello World",
            "This is plain English text",
            "123456789",
            "Special chars: !@#$%^&*()",
        ]

        for text in ascii_texts:
            assert detector.detect_unicode(text) is False, f"Falsely detected: {text}"

    def test_legacy_encoded_not_detected_as_unicode(self):
        """Test that legacy-encoded text is not detected as Unicode."""
        detector = EncodingDetector()

        # These are typical legacy encoding outputs
        legacy_texts = [
            "´ÖÆüÖ¸üÖÂ™Òü",
            "d`fr ns'k",
            "Hkkjr x.kjkT;",
        ]

        for text in legacy_texts:
            assert detector.detect_unicode(text) is False, f"Falsely detected: {text}"

    def test_empty_text(self):
        """Test handling of empty text."""
        detector = EncodingDetector()

        assert detector.detect_unicode("") is False
        assert detector.detect_unicode("   ") is False


class TestHeuristicDetection:
    """Tests for heuristic-based detection."""

    def test_detect_shree_lipi_heuristic(self):
        """Test heuristic detection of Shree-Lipi encoded text."""
        detector = EncodingDetector()

        # Text with Shree-Lipi signatures
        text = "´ÖÆüÖ¸üÖÂ™Òü ¸üÖ•Ö³ÖÖÂÖÖ †×¬Ö×®ÖμÖ´Ö"
        result = detector.detect_from_text_heuristic(text)

        assert result.detected_encoding == "shree-lipi"
        assert result.confidence > 0.5
        assert result.method == DetectionMethod.HEURISTIC

    def test_detect_kruti_dev_heuristic(self):
        """Test heuristic detection of Kruti Dev encoded text."""
        detector = EncodingDetector()

        # Text with Kruti Dev signatures
        text = "Hkkjr ns'k esa d`fr gS fd dh"
        result = detector.detect_from_text_heuristic(text)

        assert result.detected_encoding == "kruti-dev"
        assert result.method == DetectionMethod.HEURISTIC

    def test_detect_unicode_via_heuristic(self):
        """Test that Unicode is detected via heuristic path."""
        detector = EncodingDetector()

        text = "महाराष्ट्र राजभाषा अधिनियम"
        result = detector.detect_from_text_heuristic(text)

        assert result.detected_encoding == "unicode-devanagari"
        assert result.confidence == 1.0
        assert result.method == DetectionMethod.UNICODE_DETECTED

    def test_unknown_encoding(self):
        """Test handling of text with unknown encoding."""
        detector = EncodingDetector()

        text = "Plain English text with no special markers"
        result = detector.detect_from_text_heuristic(text)

        assert result.detected_encoding == "unknown"
        assert result.confidence == 0.0

    def test_fallback_encodings_provided(self):
        """Test that fallback encodings are provided when uncertain."""
        detector = EncodingDetector()

        # Text with some extended ASCII but no clear signatures
        text = "Some text with extended: ñ ü ö ä"
        result = detector.detect_from_text_heuristic(text)

        # Should detect as unknown-legacy with fallbacks
        if result.detected_encoding == "unknown-legacy":
            assert len(result.fallback_encodings) > 0

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        detector = EncodingDetector()

        result = detector.detect_from_text_heuristic("")
        assert result.detected_encoding == "unknown"
        assert result.confidence == 0.0


class TestFontListDetection:
    """Tests for detection from font lists."""

    def test_detect_from_font_list(self):
        """Test detection from a list of fonts."""
        detector = EncodingDetector()

        fonts = [
            FontInfo(name="Arial"),
            FontInfo(name="Shree-Dev-0714"),
            FontInfo(name="Times New Roman"),
        ]

        result = detector.detect_from_fonts(fonts)
        assert result is not None
        assert result.detected_encoding == "shree-dev"

    def test_no_legacy_fonts_in_list(self):
        """Test when no legacy or Devanagari fonts are in the list."""
        detector = EncodingDetector()

        fonts = [
            FontInfo(name="Arial"),
            FontInfo(name="Helvetica"),
            FontInfo(name="Times New Roman"),
        ]

        result = detector.detect_from_fonts(fonts)
        assert result is None

    def test_unicode_devanagari_font_in_list(self):
        """Test when Unicode Devanagari fonts are in the list."""
        detector = EncodingDetector()

        fonts = [
            FontInfo(name="Arial"),
            FontInfo(name="Mangal"),
            FontInfo(name="Times New Roman"),
        ]

        result = detector.detect_from_fonts(fonts)
        assert result is not None
        assert result.detected_encoding == "unicode-devanagari"
        assert result.is_unicode is True

    def test_empty_font_list(self):
        """Test with empty font list."""
        detector = EncodingDetector()

        result = detector.detect_from_fonts([])
        assert result is None


class TestTextBlockDetection:
    """Tests for text block detection."""

    def test_detect_from_text_block_with_font(self):
        """Test detection from text block with font name."""
        detector = EncodingDetector()

        block = TextBlock(
            raw_text="´ÖÆüÖ¸üÖÂ™Òü",
            font_name="Shree-Dev-0714",
        )

        result = detector.detect_from_text_block(block)
        assert result.detected_encoding == "shree-dev"
        assert result.method == DetectionMethod.FONT_MATCH

    def test_detect_from_text_block_without_font(self):
        """Test detection from text block without font name."""
        detector = EncodingDetector()

        block = TextBlock(raw_text="´ÖÆüÖ¸üÖÂ™Òü Æü Ö¸ü")

        result = detector.detect_from_text_block(block)
        # Should fall back to heuristic
        assert result.method == DetectionMethod.HEURISTIC

    def test_detect_unicode_text_block(self):
        """Test detection of Unicode text block."""
        detector = EncodingDetector()

        block = TextBlock(
            raw_text="महाराष्ट्र राजभाषा",
            font_name="Mangal",  # Unicode font
        )

        result = detector.detect_from_text_block(block)
        # Mangal won't match legacy patterns, should detect Unicode via heuristic
        assert result.is_unicode


class TestDocumentDetection:
    """Tests for full document detection."""

    def test_detect_from_simple_document(self):
        """Test detection from a simple document."""
        detector = EncodingDetector()

        # Create a document with legacy-encoded text
        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[
                        TextBlock(
                            raw_text="´ÖÆüÖ¸üÖÂ™Òü",
                            font_name="Shree-Dev-0714",
                        )
                    ],
                ),
                PDFPage(
                    page_number=2,
                    text_blocks=[
                        TextBlock(
                            raw_text="More text Æü Ö¸ü",
                            font_name="Shree-Dev-0714",
                        )
                    ],
                ),
            ],
            fonts=[FontInfo(name="Shree-Dev-0714")],
        )

        overall, page_results = detector.detect_from_document(doc)

        assert overall.detected_encoding == "shree-dev"
        assert overall.is_legacy
        assert len(page_results) == 2
        assert 1 in page_results
        assert 2 in page_results

    def test_detect_mixed_encoding_document(self):
        """Test detection from document with mixed encodings."""
        detector = EncodingDetector()

        # Create a document with mixed encodings
        doc = PDFDocument(
            filepath=Path("/test/mixed.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[
                        TextBlock(
                            raw_text="महाराष्ट्र",  # Unicode
                            font_name="Mangal",
                        )
                    ],
                ),
                PDFPage(
                    page_number=2,
                    text_blocks=[
                        TextBlock(
                            raw_text="´ÖÆüÖ¸üÖÂ™Òü",
                            font_name="Shree-Dev-0714",
                        )
                    ],
                ),
            ],
        )

        overall, page_results = detector.detect_from_document(doc)

        # Page results should differ
        assert len(page_results) == 2
        assert page_results[1].is_unicode
        assert page_results[2].is_legacy

    def test_detect_empty_document(self):
        """Test detection from empty document."""
        detector = EncodingDetector()

        doc = PDFDocument(
            filepath=Path("/test/empty.pdf"),
            pages=[],
        )

        overall, page_results = detector.detect_from_document(doc)

        assert overall.detected_encoding == "unknown"
        assert overall.confidence == 0.0
        assert len(page_results) == 0

    def test_document_with_font_metadata(self):
        """Test that document-level font metadata is used."""
        detector = EncodingDetector()

        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[TextBlock(raw_text="Some text")],
                )
            ],
            fonts=[FontInfo(name="Shree-Dev-0714")],
        )

        overall, page_results = detector.detect_from_document(doc)

        # Should detect from document fonts
        assert overall.detected_encoding == "shree-dev"


class TestConvenienceFunction:
    """Tests for the detect_encoding convenience function."""

    def test_detect_with_font_name(self):
        """Test detection with font name."""
        result = detect_encoding(font_name="Shree-Dev-0714")
        assert result.detected_encoding == "shree-dev"

    def test_detect_with_text(self):
        """Test detection with text."""
        result = detect_encoding(text="महाराष्ट्र राजभाषा")
        assert result.is_unicode

    def test_detect_with_document(self):
        """Test detection with document."""
        doc = PDFDocument(
            filepath=Path("/test/doc.pdf"),
            pages=[
                PDFPage(
                    page_number=1,
                    text_blocks=[
                        TextBlock(
                            raw_text="´ÖÆüÖ¸üÖÂ™Òü",
                            font_name="Shree-Dev-0714",
                        )
                    ],
                )
            ],
        )

        result = detect_encoding(document=doc)
        assert result.detected_encoding == "shree-dev"

    def test_detect_with_nothing(self):
        """Test detection with no input."""
        result = detect_encoding()
        assert result.detected_encoding == "unknown"
        assert result.confidence == 0.0


class TestEncodingDetectionResult:
    """Tests for EncodingDetectionResult properties."""

    def test_is_unicode_property(self):
        """Test is_unicode property."""
        unicode_result = EncodingDetectionResult(
            detected_encoding="unicode-devanagari",
            confidence=1.0,
            method=DetectionMethod.UNICODE_DETECTED,
        )
        legacy_result = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )

        assert unicode_result.is_unicode is True
        assert legacy_result.is_unicode is False

    def test_is_legacy_property(self):
        """Test is_legacy property."""
        legacy_result = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )
        unknown_result = EncodingDetectionResult(
            detected_encoding="unknown",
            confidence=0.0,
            method=DetectionMethod.HEURISTIC,
        )

        assert legacy_result.is_legacy is True
        assert unknown_result.is_legacy is False

    def test_is_high_confidence_property(self):
        """Test is_high_confidence property."""
        high = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.95,
            method=DetectionMethod.FONT_MATCH,
        )
        low = EncodingDetectionResult(
            detected_encoding="shree-lipi",
            confidence=0.6,
            method=DetectionMethod.HEURISTIC,
        )

        assert high.is_high_confidence is True
        assert low.is_high_confidence is False
