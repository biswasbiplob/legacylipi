"""Pydantic request/response schemas for the LegacyLipi API."""

from typing import Literal

from pydantic import BaseModel, Field

# --- Request schemas ---


class ScanCopyRequest(BaseModel):
    dpi: int = 300
    color_mode: Literal["color", "grayscale", "bw"] = "color"
    quality: int = Field(85, ge=1, le=100)


class ConvertRequest(BaseModel):
    ocr_engine: Literal["easyocr", "tesseract"] = "easyocr"
    ocr_lang: str = "mar"
    ocr_dpi: int = 300
    output_format: Literal["pdf", "text", "markdown"] = "pdf"


class TranslateRequest(BaseModel):
    target_lang: str = "en"
    output_format: Literal["pdf", "text", "markdown"] = "pdf"
    translation_mode: Literal["structure_preserving", "flowing"] = "structure_preserving"
    translator: str = "trans"
    use_ocr: bool = False
    ocr_engine: Literal["easyocr", "tesseract"] = "easyocr"
    ocr_lang: str = "mar"
    ocr_dpi: int = 300
    openai_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3.2"
    ollama_host: str = "http://localhost:11434"
    trans_path: str | None = None
    gcp_project: str | None = None


# --- Response schemas ---


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    file_size: int


class JobResponse(BaseModel):
    job_id: str


class ProgressEvent(BaseModel):
    status: Literal["processing", "complete", "error"]
    percent: int = 0
    step: str = ""
    message: str = ""
    filename: str | None = None
    file_size: int | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = ""


class ErrorResponse(BaseModel):
    detail: str
