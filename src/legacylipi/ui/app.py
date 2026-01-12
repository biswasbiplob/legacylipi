"""LegacyLipi Web UI using NiceGUI.

A web interface for translating PDFs with legacy Indian font encodings.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from nicegui import ui, app

# Language options
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

OUTPUT_FORMATS = {
    "pdf": "PDF",
    "text": "Text",
    "markdown": "Markdown",
}

TRANSLATORS = {
    "google": "Google Translate (Free)",
    "mymemory": "MyMemory (Free)",
    "trans": "Translate-Shell (CLI)",
    "ollama": "Ollama (Local LLM)",
    "openai": "OpenAI (API Key Required)",
}

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
OLLAMA_MODELS = ["llama3.2", "llama3.1", "llama2", "mistral", "phi", "gemma"]


class TranslationUI:
    """Main UI class for LegacyLipi translation interface."""

    def __init__(self):
        self.uploaded_file: Optional[bytes] = None
        self.uploaded_filename: Optional[str] = None
        self.result_content: Optional[bytes] = None
        self.result_filename: Optional[str] = None
        self.is_translating: bool = False

        # UI state
        self.target_lang = "en"
        self.output_format = "pdf"
        self.use_ocr = False
        self.ocr_lang = "mar"
        self.ocr_dpi = 300
        self.translator = "google"
        self.openai_key = ""
        self.openai_model = "gpt-4o-mini"
        self.ollama_model = "llama3.2"
        self.ollama_host = "http://localhost:11434"
        self.trans_path = ""

        # UI elements
        self.progress_bar = None
        self.status_label = None
        self.download_button = None
        self.translate_button = None
        self.ocr_options_container = None
        self.translator_options_container = None

    def build(self):
        """Build the main UI."""
        ui.dark_mode().enable()

        with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-4"):
            # Header
            with ui.row().classes("w-full items-center justify-center gap-2"):
                ui.icon("translate", size="lg", color="primary")
                ui.label("LegacyLipi").classes("text-2xl font-bold")
            ui.label("PDF Translator for Legacy Indian Font Encodings").classes(
                "text-center text-gray-400 mb-4"
            )

            # File upload section
            with ui.card().classes("w-full"):
                ui.label("Upload PDF").classes("text-lg font-semibold mb-2")
                ui.upload(
                    label="Drop PDF here or click to upload",
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    max_file_size=50_000_000,  # 50MB
                ).props('accept=".pdf"').classes("w-full")

                self.file_label = ui.label("No file selected").classes("text-gray-400 text-sm mt-2")

            # Translation settings
            with ui.card().classes("w-full"):
                ui.label("Translation Settings").classes("text-lg font-semibold mb-2")

                with ui.row().classes("w-full gap-4"):
                    ui.select(
                        label="Target Language",
                        options=TARGET_LANGUAGES,
                        value=self.target_lang,
                        on_change=lambda e: setattr(self, "target_lang", e.value),
                    ).classes("flex-1")

                    ui.select(
                        label="Output Format",
                        options=OUTPUT_FORMATS,
                        value=self.output_format,
                        on_change=lambda e: setattr(self, "output_format", e.value),
                    ).classes("flex-1")

            # OCR settings
            with ui.card().classes("w-full"):
                ui.label("OCR Settings").classes("text-lg font-semibold mb-2")

                ui.checkbox(
                    "Use OCR (for scanned/image PDFs)",
                    value=self.use_ocr,
                    on_change=self._toggle_ocr,
                )

                self.ocr_options_container = ui.column().classes("w-full gap-2 mt-2")
                self._build_ocr_options()

            # Translator settings
            with ui.card().classes("w-full"):
                ui.label("Translator").classes("text-lg font-semibold mb-2")

                ui.select(
                    label="Translation Backend",
                    options=TRANSLATORS,
                    value=self.translator,
                    on_change=self._change_translator,
                ).classes("w-full")

                self.translator_options_container = ui.column().classes("w-full gap-2 mt-2")
                self._build_translator_options()

            # Translate button
            self.translate_button = ui.button(
                "Translate",
                on_click=self._translate,
                icon="translate",
            ).props("color=primary size=lg").classes("w-full")

            # Progress section
            with ui.card().classes("w-full").bind_visibility_from(self, "is_translating"):
                self.progress_bar = ui.linear_progress(value=0, show_value=True).classes("w-full")
                self.status_label = ui.label("Starting...").classes("text-center text-gray-400")

            # Download section
            self.download_card = ui.card().classes("w-full")
            self.download_card.set_visibility(False)
            with self.download_card:
                ui.label("Translation Complete!").classes("text-lg font-semibold text-green-500 mb-2")
                self.download_button = ui.button(
                    "Download Result",
                    on_click=self._download_result,
                    icon="download",
                ).props("color=positive size=lg").classes("w-full")

    def _build_ocr_options(self):
        """Build OCR-specific options."""
        self.ocr_options_container.clear()

        if not self.use_ocr:
            with self.ocr_options_container:
                ui.label("OCR is disabled. Enable to configure.").classes("text-gray-500 text-sm")
            return

        with self.ocr_options_container:
            with ui.row().classes("w-full gap-4"):
                ui.select(
                    label="OCR Language",
                    options=OCR_LANGUAGES,
                    value=self.ocr_lang,
                    on_change=lambda e: setattr(self, "ocr_lang", e.value),
                ).classes("flex-1")

                ui.number(
                    label="DPI",
                    value=self.ocr_dpi,
                    min=100,
                    max=600,
                    step=50,
                    on_change=lambda e: setattr(self, "ocr_dpi", int(e.value)),
                ).classes("flex-1")

    def _toggle_ocr(self, e):
        """Toggle OCR mode."""
        self.use_ocr = e.value
        self._build_ocr_options()
        self.ocr_options_container.update()

    def _build_translator_options(self):
        """Build translator-specific options based on selected translator."""
        self.translator_options_container.clear()

        with self.translator_options_container:
            if self.translator == "openai":
                ui.input(
                    label="OpenAI API Key",
                    value=self.openai_key,
                    password=True,
                    password_toggle_button=True,
                    on_change=lambda e: setattr(self, "openai_key", e.value),
                ).classes("w-full")

                ui.select(
                    label="Model",
                    options=OPENAI_MODELS,
                    value=self.openai_model,
                    on_change=lambda e: setattr(self, "openai_model", e.value),
                ).classes("w-full")

            elif self.translator == "ollama":
                ui.select(
                    label="Model",
                    options=OLLAMA_MODELS,
                    value=self.ollama_model,
                    on_change=lambda e: setattr(self, "ollama_model", e.value),
                ).classes("w-full")

                ui.input(
                    label="Ollama Host (optional)",
                    value=self.ollama_host,
                    placeholder="http://localhost:11434",
                    on_change=lambda e: setattr(self, "ollama_host", e.value),
                ).classes("w-full")

            elif self.translator == "trans":
                ui.input(
                    label="Trans Executable Path (optional)",
                    value=self.trans_path,
                    placeholder="Leave empty to auto-detect",
                    on_change=lambda e: setattr(self, "trans_path", e.value),
                ).classes("w-full")

            elif self.translator in ("google", "mymemory"):
                ui.label("No additional configuration required.").classes("text-gray-500 text-sm")

    def _change_translator(self, e):
        """Handle translator change."""
        self.translator = e.value
        self._build_translator_options()

    async def _handle_upload(self, e):
        """Handle file upload."""
        try:
            # read() is async in NiceGUI 3.x
            self.uploaded_file = await e.file.read()
            self.uploaded_filename = e.file.name
            file_size = len(self.uploaded_file) / 1024
            self.file_label.set_text(f"Selected: {e.file.name} ({file_size:.1f} KB)")

            # Reset result
            self.result_content = None
            self.result_filename = None
            self.download_card.set_visibility(False)

            ui.notify(f"File '{e.file.name}' uploaded successfully!", type="positive")
        except Exception as ex:
            ui.notify(f"Upload error: {ex}", type="negative")

    async def _translate(self):
        """Run the translation pipeline."""
        if not self.uploaded_file:
            ui.notify("Please upload a PDF file first.", type="warning")
            return

        if self.translator == "openai" and not self.openai_key:
            ui.notify("Please enter your OpenAI API key.", type="warning")
            return

        self.is_translating = True
        self.translate_button.disable()
        self.download_card.set_visibility(False)

        try:
            # Import here to avoid circular imports and ensure deps are loaded
            from legacylipi.core.encoding_detector import EncodingDetector
            from legacylipi.core.models import DetectionMethod, EncodingDetectionResult, OutputFormat
            from legacylipi.core.output_generator import OutputGenerator
            from legacylipi.core.pdf_parser import parse_pdf
            from legacylipi.core.translator import create_translator
            from legacylipi.core.unicode_converter import UnicodeConverter

            # Create temp file for input
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(self.uploaded_file)
                input_path = Path(tmp.name)

            try:
                # Step 1: Parse PDF
                self.progress_bar.set_value(0.1)
                self.status_label.set_text("Parsing PDF...")
                await asyncio.sleep(0.1)  # Allow UI to update

                # Get event loop for running blocking operations
                loop = asyncio.get_event_loop()

                if self.use_ocr:
                    from legacylipi.core.ocr_parser import parse_pdf_with_ocr

                    # Run OCR in executor to avoid blocking the event loop
                    document = await loop.run_in_executor(
                        None,
                        lambda: parse_pdf_with_ocr(input_path, lang=self.ocr_lang, dpi=self.ocr_dpi)
                    )
                    encoding_result = EncodingDetectionResult(
                        detected_encoding="unicode-ocr",
                        confidence=1.0,
                        method=DetectionMethod.UNICODE_DETECTED,
                    )
                    converted_doc = document
                else:
                    # Run PDF parsing in executor to avoid blocking
                    document = await loop.run_in_executor(None, lambda: parse_pdf(input_path))

                    # Step 2: Detect encoding
                    self.progress_bar.set_value(0.2)
                    self.status_label.set_text("Detecting encoding...")
                    await asyncio.sleep(0.1)

                    detector = EncodingDetector()
                    # Run encoding detection in executor
                    encoding_result, page_encodings = await loop.run_in_executor(
                        None,
                        lambda: detector.detect_from_document(document)
                    )

                    # Step 3: Convert to Unicode
                    self.progress_bar.set_value(0.3)
                    self.status_label.set_text("Converting to Unicode...")
                    await asyncio.sleep(0.1)

                    converter = UnicodeConverter()
                    # Run Unicode conversion in executor
                    converted_doc = await loop.run_in_executor(
                        None,
                        lambda: converter.convert_document(document, page_encodings=page_encodings)
                    )

                # Step 4: Translate
                self.progress_bar.set_value(0.4)
                self.status_label.set_text(f"Translating with {self.translator}...")
                await asyncio.sleep(0.1)

                # Build translator kwargs
                translator_kwargs = {}
                if self.translator == "openai":
                    translator_kwargs["api_key"] = self.openai_key
                    translator_kwargs["model"] = self.openai_model
                elif self.translator == "ollama":
                    translator_kwargs["model"] = self.ollama_model
                    if self.ollama_host:
                        translator_kwargs["host"] = self.ollama_host
                elif self.translator == "trans" and self.trans_path:
                    translator_kwargs["trans_path"] = self.trans_path

                engine = create_translator(self.translator, **translator_kwargs)

                # Build text with page markers
                text_parts = []
                for i, page in enumerate(converted_doc.pages, 1):
                    page_text = page.unicode_text
                    text_parts.append(f"--- Page {i} ---\n{page_text}")
                unicode_text = "\n\n".join(text_parts)

                # Run translation (this is sync, wrap in executor)
                translation_result = await loop.run_in_executor(
                    None,
                    lambda: engine.translate(unicode_text, source_lang="mr", target_lang=self.target_lang),
                )

                self.progress_bar.set_value(0.8)
                self.status_label.set_text("Generating output...")
                await asyncio.sleep(0.1)

                # Step 5: Generate output
                fmt_map = {"pdf": OutputFormat.PDF, "text": OutputFormat.TEXT, "markdown": OutputFormat.MARKDOWN}
                output_fmt = fmt_map.get(self.output_format, OutputFormat.TEXT)

                generator = OutputGenerator()
                output_content = generator.generate(
                    converted_doc,
                    encoding_result,
                    translation_result,
                    output_fmt,
                )

                # Store result
                if isinstance(output_content, bytes):
                    self.result_content = output_content
                else:
                    self.result_content = output_content.encode("utf-8")

                ext_map = {"pdf": ".pdf", "text": ".txt", "markdown": ".md"}
                ext = ext_map.get(self.output_format, ".txt")
                base_name = Path(self.uploaded_filename).stem
                self.result_filename = f"{base_name}_translated{ext}"

                self.progress_bar.set_value(1.0)
                self.status_label.set_text("Complete!")

                ui.notify("Translation completed successfully!", type="positive")
                self.download_card.set_visibility(True)

            finally:
                # Clean up temp file
                input_path.unlink(missing_ok=True)

        except Exception as e:
            ui.notify(f"Translation failed: {str(e)}", type="negative")
            self.status_label.set_text(f"Error: {str(e)}")

        finally:
            self.is_translating = False
            self.translate_button.enable()

    def _download_result(self):
        """Trigger download of the result file."""
        if self.result_content and self.result_filename:
            ui.download(self.result_content, self.result_filename)


def main():
    """Main entry point for the UI."""

    @ui.page("/")
    def index():
        # Create a new TranslationUI instance for each page/client
        # to ensure proper state isolation
        translation_ui = TranslationUI()
        translation_ui.build()

    ui.run(
        title="LegacyLipi - PDF Translator",
        port=8080,
        reload=False,
        show=True,
    )


if __name__ == "__main__":
    main()
