"""Language utility functions for mapping encodings to source languages."""

# Mapping from encoding name to ISO 639-1 language code
ENCODING_LANGUAGE_MAP: dict[str, str] = {
    "shree-dev": "mr",
    "shree-dev-0714": "mr",
    "shree-dev-0708": "mr",
    "shree-lipi": "mr",
    "dvb-tt": "mr",
    "shusha": "mr",
    "kruti-dev": "hi",
    "chanakya": "hi",
    "aps-dv": "hi",
    "walkman-chanakya": "hi",
    "agra": "hi",
    "akruti": "hi",
    "unicode-devanagari": "hi",
    "unicode-ocr": "hi",
}

# Default source language when encoding is unknown
DEFAULT_SOURCE_LANGUAGE = "mr"


def get_source_language(encoding_name: str) -> str:
    """Get the source language code for a detected encoding.

    Args:
        encoding_name: The detected encoding name.

    Returns:
        ISO 639-1 language code (e.g., 'mr' for Marathi, 'hi' for Hindi).
    """
    return ENCODING_LANGUAGE_MAP.get(encoding_name.lower(), DEFAULT_SOURCE_LANGUAGE)
