"""LegacyLipi Web UI using NiceGUI.

A web interface for translating PDFs with legacy Indian font encodings.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from queue import Queue, Empty
from typing import Callable, Optional

from nicegui import ui, app

logger = logging.getLogger(__name__)

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

OCR_ENGINES = {
    "easyocr": "EasyOCR (FREE - Recommended)",
    "tesseract": "Tesseract (FREE - requires install)",
}

OUTPUT_FORMATS = {
    "pdf": "PDF",
    "text": "Text",
    "markdown": "Markdown",
}

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

OPENAI_MODELS = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
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
        self.ocr_engine = "easyocr"  # Default to free EasyOCR
        self.ocr_lang = "mar"
        self.ocr_dpi = 300
        self.translator = "trans"
        self.translation_mode = "structure_preserving"  # Default to structure-preserving
        self.openai_key = ""
        self.openai_model = "gpt-4o-mini"
        self.ollama_model = "llama3.2"
        self.ollama_host = "http://localhost:11434"
        self.trans_path = ""
        self.gcp_project = ""

        # UI elements
        self.progress_bar = None
        self.status_label = None
        self.download_button = None
        self.translate_button = None
        self.ocr_options_container = None
        self.translator_options_container = None
        self.idle_container = None
        self.progress_container = None
        self.complete_container = None

        # Queue-based progress updates to prevent WebSocket disconnection
        self._progress_queue: Queue = Queue()
        self._progress_timer = None

    def _safe_ui_update(self, update_fn: Callable[[], None]) -> bool:
        """Execute UI update, returning False if client disconnected.

        This prevents crashes when async operations try to update UI elements
        after the browser client has disconnected (tab closed, page refresh, etc.).
        """
        try:
            update_fn()
            return True
        except RuntimeError as e:
            if "deleted" in str(e).lower():
                logger.warning(f"Client disconnected during UI update: {e}")
                return False  # Client disconnected, skip update
            raise  # Re-raise other RuntimeErrors

    def _poll_progress_updates(self):
        """Poll progress queue and update UI at controlled rate.

        This decouples progress reporting from UI updates, preventing
        WebSocket disconnection from concurrent callback bursts.
        """
        try:
            if self._progress_queue.empty():
                return

            # Get latest progress only (skip intermediate updates)
            latest = None
            while not self._progress_queue.empty():
                try:
                    latest = self._progress_queue.get_nowait()
                except Empty:
                    break

            if latest:
                completed, total, progress = latest
                self._safe_ui_update(lambda: self.progress_bar.set_value(progress))
                self._safe_ui_update(lambda: self.status_label.set_text(f"Translating block {completed}/{total}..."))
        except RuntimeError as e:
            # Handle client disconnection - parent slot deleted
            if "deleted" in str(e).lower():
                logger.debug(f"Timer callback skipped - client disconnected: {e}")
            else:
                raise

    def build(self):
        """Build the main UI."""
        ui.dark_mode().enable()

        with ui.column().classes("w-full max-w-6xl mx-auto p-4 gap-4"):
            # Header
            with ui.row().classes("w-full items-center justify-center gap-2"):
                ui.icon("translate", size="lg", color="primary")
                ui.label("LegacyLipi").classes("text-2xl font-bold")
            ui.label("PDF Translator for Legacy Indian Font Encodings").classes(
                "text-center text-gray-400 mb-4"
            )

            # Two-column layout
            with ui.row().classes("w-full gap-6 items-start").style("flex-wrap: wrap;"):
                # Left column - Settings
                with ui.column().classes("gap-4").style("flex: 1 1 400px; min-width: 300px;"):
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

                        ui.select(
                            label="Translation Mode",
                            options=TRANSLATION_MODES,
                            value=self.translation_mode,
                            on_change=lambda e: setattr(self, "translation_mode", e.value),
                        ).classes("w-full mt-2")
                        ui.label(
                            "Structure Preserving keeps original layout and scales fonts to fit"
                        ).classes("text-xs text-gray-500")

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

                # Right column - Status Panel
                with ui.column().classes("gap-4").style("flex: 1 1 400px; min-width: 300px;"):
                    with ui.card().classes("w-full min-h-80"):
                        ui.label("Status").classes("text-lg font-semibold mb-4")

                        # Idle state container
                        self.idle_container = ui.column().classes("w-full items-center gap-2")
                        with self.idle_container:
                            ui.icon("info", size="xl", color="grey")
                            ui.label("Ready to translate").classes("text-xl text-gray-400 mt-2")
                            with ui.column().classes("mt-4 gap-1"):
                                ui.label("1. Upload a PDF file").classes("text-sm text-gray-500")
                                ui.label("2. Configure translation settings").classes("text-sm text-gray-500")
                                ui.label("3. Click Translate").classes("text-sm text-gray-500")

                        # Progress state container
                        self.progress_container = ui.column().classes("w-full items-center gap-4")
                        self.progress_container.bind_visibility_from(self, "is_translating")
                        with self.progress_container:
                            ui.icon("hourglass_empty", size="xl", color="primary")
                            self.status_label = ui.label("Starting...").classes("text-lg text-gray-400")
                            self.progress_bar = ui.linear_progress(value=0, show_value=True).classes("w-full")

                        # Timer for polling progress queue (100ms interval for smooth updates)
                        self._progress_timer = ui.timer(0.1, callback=self._poll_progress_updates, active=False)

                        # Complete state container
                        self.complete_container = ui.column().classes("w-full items-center gap-4")
                        self.complete_container.set_visibility(False)
                        with self.complete_container:
                            ui.icon("check_circle", size="xl", color="green")
                            ui.label("Translation Complete!").classes("text-xl text-green-500")
                            self.download_button = ui.button(
                                "Download Result",
                                on_click=self._download_result,
                                icon="download",
                            ).props("color=positive size=lg").classes("w-full max-w-xs")

    def _build_ocr_options(self):
        """Build OCR-specific options."""
        self.ocr_options_container.clear()

        if not self.use_ocr:
            with self.ocr_options_container:
                ui.label("OCR is disabled. Enable to configure.").classes("text-gray-500 text-sm")
            return

        with self.ocr_options_container:
            ui.select(
                label="OCR Engine",
                options=OCR_ENGINES,
                value=self.ocr_engine,
                on_change=lambda e: setattr(self, "ocr_engine", e.value),
            ).classes("w-full")
            ui.label(
                "EasyOCR: Free, uses deep learning, downloads models on first use (~100MB)"
            ).classes("text-xs text-gray-500")

            with ui.row().classes("w-full gap-4 mt-2"):
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
                    on_change=lambda e: setattr(self, "ocr_dpi", int(e.value)) if e.value is not None else None,
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

            elif self.translator == "gcp_cloud":
                ui.input(
                    label="GCP Project ID",
                    value=self.gcp_project,
                    placeholder="my-gcp-project-id",
                    on_change=lambda e: setattr(self, "gcp_project", e.value),
                ).classes("w-full")
                ui.label(
                    "Free tier: 500,000 chars/month. Requires GOOGLE_APPLICATION_CREDENTIALS."
                ).classes("text-xs text-gray-500")

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

            # Reset result and show idle state
            self.result_content = None
            self.result_filename = None
            self.complete_container.set_visibility(False)
            self.idle_container.set_visibility(True)

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

        if self.translator == "gcp_cloud" and not self.gcp_project:
            # Try to get from environment
            import os
            if not os.environ.get("GCP_PROJECT_ID"):
                ui.notify("Please enter your GCP Project ID.", type="warning")
                return

        self.is_translating = True
        self.translate_button.disable()
        self.idle_container.set_visibility(False)
        self.complete_container.set_visibility(False)

        logger.info(
            f"Starting translation: file={self.uploaded_filename}, "
            f"translator={self.translator}, mode={self.translation_mode}, "
            f"output={self.output_format}, ocr={self.use_ocr}, ocr_engine={self.ocr_engine}"
        )

        try:
            # Import here to avoid circular imports and ensure deps are loaded
            from legacylipi.core.encoding_detector import EncodingDetector
            from legacylipi.core.models import DetectionMethod, EncodingDetectionResult, OutputFormat
            from legacylipi.core.output_generator import OutputGenerator
            from legacylipi.core.pdf_parser import parse_pdf
            from legacylipi.core.translator import create_translator, UsageLimitExceededError
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
                    # Select OCR engine based on user choice
                    if self.ocr_engine == "easyocr":
                        from legacylipi.core.ocr_parser import parse_pdf_with_easyocr

                        self.status_label.set_text("Running EasyOCR (first run downloads models)...")
                        # Run EasyOCR in executor to avoid blocking the event loop
                        document = await loop.run_in_executor(
                            None,
                            lambda: parse_pdf_with_easyocr(input_path, lang=self.ocr_lang, dpi=self.ocr_dpi)
                        )
                    else:
                        from legacylipi.core.ocr_parser import parse_pdf_with_ocr

                        self.status_label.set_text("Running Tesseract OCR...")
                        # Run Tesseract in executor to avoid blocking the event loop
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
                elif self.translator == "gcp_cloud":
                    import os
                    project_id = self.gcp_project or os.environ.get("GCP_PROJECT_ID")
                    if project_id:
                        translator_kwargs["project_id"] = project_id

                engine = create_translator(self.translator, **translator_kwargs)

                # Check translation mode
                use_structure_preserving = (
                    self.translation_mode == "structure_preserving"
                    and self.output_format == "pdf"
                )

                translation_result = None

                if use_structure_preserving:
                    # Structure-preserving mode: translate each block individually
                    # Collect all blocks with position data
                    all_blocks = []
                    for page in converted_doc.pages:
                        for block in page.text_blocks:
                            if block.position is not None:
                                all_blocks.append(block)

                    if all_blocks:
                        total_blocks = len(all_blocks)
                        logger.info(f"Structure-preserving mode: {total_blocks} blocks to translate")
                        self.status_label.set_text(f"Translating {total_blocks} text blocks...")

                        # Progress callback for block translation - queues updates instead of direct UI calls
                        # This prevents WebSocket disconnection from concurrent callback bursts
                        def update_progress(completed: int, total: int):
                            progress = 0.4 + (0.4 * completed / total)
                            # Log every 50 blocks or at completion
                            if completed % 50 == 0 or completed == total:
                                logger.info(f"Translation progress: {completed}/{total} blocks ({progress*100:.1f}%)")
                            # Queue progress update - timer will poll and update UI at controlled rate
                            self._progress_queue.put((completed, total, progress))

                        # Start progress timer before translation
                        if self._progress_timer:
                            self._progress_timer.active = True

                        # Translate blocks concurrently with rate limiting
                        try:
                            await engine.translate_blocks_async(
                                all_blocks,
                                source_lang="mr",
                                target_lang=self.target_lang,
                                max_concurrent=3,
                                progress_callback=update_progress,
                            )
                            # Check if any blocks were actually translated
                            translated_count = sum(1 for b in all_blocks if b.translated_text and b.translated_text != (b.unicode_text or b.raw_text))
                            if translated_count == 0:
                                self._safe_ui_update(lambda: ui.notify("Warning: No blocks were translated. Check API key and model.", type="warning"))
                        except UsageLimitExceededError as e:
                            self._safe_ui_update(lambda e=e: ui.notify(
                                f"GCP free tier limit exceeded: {e.current_usage:,}/{e.limit:,} chars. "
                                f"Need {e.requested:,} more. Try a different translator.",
                                type="warning",
                                timeout=10000,
                            ))
                            raise
                        except Exception as e:
                            self._safe_ui_update(lambda e=e: ui.notify(f"Translation error: {e}", type="negative"))
                            raise
                    else:
                        # No positioned blocks - fall back to flowing mode
                        use_structure_preserving = False

                if not use_structure_preserving:
                    # Flowing mode: combine text and translate as one string
                    text_parts = []
                    for i, page in enumerate(converted_doc.pages, 1):
                        page_text = page.unicode_text
                        text_parts.append(f"--- Page {i} ---\n{page_text}")
                    unicode_text = "\n\n".join(text_parts)

                    # Run translation (this is sync, wrap in executor)
                    try:
                        translation_result = await loop.run_in_executor(
                            None,
                            lambda: engine.translate(unicode_text, source_lang="mr", target_lang=self.target_lang),
                        )
                        if not translation_result or not translation_result.translated_text:
                            self._safe_ui_update(lambda: ui.notify("Warning: Translation returned empty result. Check API key and model.", type="warning"))
                    except UsageLimitExceededError as e:
                        self._safe_ui_update(lambda e=e: ui.notify(
                            f"GCP free tier limit exceeded: {e.current_usage:,}/{e.limit:,} chars. "
                            f"Need {e.requested:,} more. Try a different translator.",
                            type="warning",
                            timeout=10000,
                        ))
                        raise
                    except Exception as e:
                        self._safe_ui_update(lambda e=e: ui.notify(f"Translation error: {e}", type="negative"))
                        raise

                self._safe_ui_update(lambda: self.progress_bar.set_value(0.8))
                self._safe_ui_update(lambda: self.status_label.set_text("Generating output..."))
                await asyncio.sleep(0.1)

                # Step 5: Generate output
                fmt_map = {"pdf": OutputFormat.PDF, "text": OutputFormat.TEXT, "markdown": OutputFormat.MARKDOWN}
                output_fmt = fmt_map.get(self.output_format, OutputFormat.TEXT)

                generator = OutputGenerator()

                if use_structure_preserving and output_fmt == OutputFormat.PDF:
                    # Use structure-preserving PDF generation
                    output_content = generator.generate_pdf(
                        converted_doc,
                        encoding_result,
                        translation_result=None,
                        structure_preserving_translation=True,
                    )
                else:
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

                self._safe_ui_update(lambda: self.progress_bar.set_value(1.0))
                self._safe_ui_update(lambda: self.status_label.set_text("Complete!"))

                logger.info(
                    f"Translation completed successfully: output={self.result_filename}, "
                    f"size={len(self.result_content)} bytes"
                )

                self._safe_ui_update(lambda: ui.notify("Translation completed successfully!", type="positive"))
                self._safe_ui_update(lambda: self.complete_container.set_visibility(True))

            finally:
                # Clean up temp file
                input_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(
                f"Translation failed: {e}",
                exc_info=True,
                extra={
                    "file": self.uploaded_filename,
                    "translator": self.translator,
                    "mode": self.translation_mode,
                }
            )
            self._safe_ui_update(lambda e=e: ui.notify(f"Translation failed: {str(e)}", type="negative"))
            self._safe_ui_update(lambda e=e: self.status_label.set_text(f"Error: {str(e)}"))
            # Show idle state again on error so user can retry
            self._safe_ui_update(lambda: self.idle_container.set_visibility(True))

        finally:
            self.is_translating = False
            # Stop progress timer
            if self._progress_timer:
                self._progress_timer.active = False
            # Clear any remaining items in progress queue
            while not self._progress_queue.empty():
                try:
                    self._progress_queue.get_nowait()
                except Empty:
                    break
            logger.debug("Translation task finished, re-enabling UI")
            self._safe_ui_update(lambda: self.translate_button.enable())

    def _download_result(self):
        """Trigger download of the result file."""
        if self.result_content and self.result_filename:
            ui.download(self.result_content, self.result_filename)


def main():
    """Main entry point for the UI."""
    # Configure logging to show in terminal
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Starting LegacyLipi UI server...")

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
        reconnect_timeout=30.0,  # Increased from default 3s to handle long translations
    )


if __name__ == "__main__":
    main()
