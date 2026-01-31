"""Centralized language code mappings for translation backends."""

# Full language names (used for prompts and display)
LANGUAGE_NAMES: dict[str, str] = {
    "mr": "Marathi",
    "hi": "Hindi",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "bn": "Bengali",
    "pa": "Punjabi",
    "san": "Sanskrit",
    "auto": "Auto-detect",
}

# Google Translate codes (maps our codes to Google's)
GOOGLE_LANGUAGE_CODES: dict[str, str] = {
    "marathi": "mr",
    "hindi": "hi",
    "english": "en",
    "auto": "auto",
    # Most codes are same as ours
}

# MyMemory BCP-47 codes
MYMEMORY_LANGUAGE_CODES: dict[str, str] = {
    "mr": "mr-IN",
    "hi": "hi-IN",
    "en": "en-GB",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "pa": "pa-IN",
}

# Tesseract OCR language codes
TESSERACT_LANGUAGE_CODES: dict[str, str] = {
    "mr": "mar",
    "hi": "hin",
    "ta": "tam",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "bn": "ben",
    "gu": "guj",
    "pa": "pan",
    "san": "san",
}


def get_language_name(code: str) -> str:
    """Get full language name from code.

    Args:
        code: Language code (e.g., 'mr', 'hi').

    Returns:
        Full language name, or the code itself if not found.
    """
    return LANGUAGE_NAMES.get(code.lower(), code)


def get_google_code(code: str) -> str:
    """Map language code to Google Translate format.

    Args:
        code: Language code or name.

    Returns:
        Google Translate compatible code.
    """
    code_lower = code.lower()
    # Check if it's a name that needs mapping
    if code_lower in GOOGLE_LANGUAGE_CODES:
        return GOOGLE_LANGUAGE_CODES[code_lower]
    # Otherwise return as-is (most codes are compatible)
    return code_lower


def get_mymemory_code(code: str) -> str:
    """Map language code to MyMemory BCP-47 format.

    Args:
        code: Language code.

    Returns:
        MyMemory BCP-47 compatible code.
    """
    code_lower = code.lower()
    return MYMEMORY_LANGUAGE_CODES.get(code_lower, code_lower)


def get_tesseract_code(code: str) -> str:
    """Map language code to Tesseract OCR format.

    Args:
        code: Language code.

    Returns:
        Tesseract compatible code.
    """
    code_lower = code.lower()
    return TESSERACT_LANGUAGE_CODES.get(code_lower, code_lower)
