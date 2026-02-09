"""Configuration endpoints — expose available options to the frontend."""

from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["config"])

TARGET_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}

OCR_LANGUAGES = {
    "mar": "Marathi",
    "hin": "Hindi",
    "tam": "Tamil",
    "tel": "Telugu",
    "kan": "Kannada",
    "mal": "Malayalam",
    "ben": "Bengali",
    "guj": "Gujarati",
    "pan": "Punjabi",
    "san": "Sanskrit",
}

OCR_ENGINES = {
    "easyocr": "EasyOCR (FREE - Recommended)",
    "tesseract": "Tesseract (FREE - requires install)",
}

OUTPUT_FORMATS = {"pdf": "PDF", "text": "Text", "markdown": "Markdown"}

TRANSLATORS = {
    "trans": "Translate-Shell (CLI) - Recommended",
    "gcp_cloud": "Google Cloud Translation (500K free/month)",
    "google": "Google Translate (Free)",
    "mymemory": "MyMemory (Free)",
    "ollama": "Ollama (Local LLM)",
    "openai": "OpenAI (API Key Required)",
}

TRANSLATION_MODES = {
    "structure_preserving": "Structure Preserving (Maintains Layout)",
    "flowing": "Flowing Text (Standard)",
}

WORKFLOW_MODES = {
    "scan_copy": "Scanned Copy",
    "convert": "Convert to Unicode",
    "translate": "Full Translation",
}

OPENAI_MODELS = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
OLLAMA_MODELS = ["llama3.2", "llama3.1", "llama2", "mistral", "phi", "gemma"]


@router.get("/languages")
async def get_languages():
    return {"target": TARGET_LANGUAGES, "ocr": OCR_LANGUAGES}


@router.get("/translators")
async def get_translators():
    return {
        "backends": TRANSLATORS,
        "openai_models": OPENAI_MODELS,
        "ollama_models": OLLAMA_MODELS,
    }


@router.get("/options")
async def get_options():
    return {
        "output_formats": OUTPUT_FORMATS,
        "translation_modes": TRANSLATION_MODES,
        "workflow_modes": WORKFLOW_MODES,
        "ocr_engines": OCR_ENGINES,
    }
