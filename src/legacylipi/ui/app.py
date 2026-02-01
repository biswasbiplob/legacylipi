"""LegacyLipi Web UI using NiceGUI.

A web interface for translating PDFs with legacy Indian font encodings.
"""

import asyncio
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path
from queue import Empty, Queue

from nicegui import ui

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

# Output formats for convert mode (no PDF)
OUTPUT_FORMATS_CONVERT = {
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

WORKFLOW_MODES = {
    "scan_copy": "Scanned Copy",
    "convert": "Convert to Unicode",
    "translate": "Full Translation",
}

WORKFLOW_DESCRIPTIONS = {
    "scan_copy": "Create an image-based PDF copy of your document",
    "convert": "Extract text via OCR and convert to readable Unicode",
    "translate": "Full pipeline: OCR, Unicode conversion, and translation",
}

OPENAI_MODELS = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
OLLAMA_MODELS = ["llama3.2", "llama3.1", "llama2", "mistral", "phi", "gemma"]


class TranslationUI:
    """Main UI class for LegacyLipi translation interface."""

    def __init__(self):
        self.uploaded_file: bytes | None = None
        self.uploaded_filename: str | None = None
        self.result_content: bytes | None = None
        self.result_filename: str | None = None
        self.is_translating: bool = False

        # Workflow mode state
        self.workflow_mode = "translate"  # "scan_copy" | "convert" | "translate"

        # UI state
        self.target_lang = "en"
        self.output_format = "pdf"
        self.use_ocr = False
        self.ocr_only_mode = False  # Internal flag for _translate() logic
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

        # Scanned copy settings
        self.scan_dpi = 300
        self.scan_color_mode = "color"
        self.scan_quality = 85  # JPEG quality (1-100)

        # UI elements - existing
        self.progress_bar = None
        self.progress_label = None
        self.status_label = None
        self.download_button = None
        self.translate_button = None
        self.ocr_options_container = None
        self.translator_options_container = None
        self.idle_container = None
        self.progress_container = None
        self.complete_container = None

        # UI elements - new for workflow mode
        self.workflow_mode_card = None
        self.scan_copy_section = None
        self.ocr_section = None
        self.output_format_section = None
        self.translation_settings_section = None
        self.translator_section = None
        self.action_button = None
        self.mode_description = None
        self.idle_instructions = None
        self.output_format_select = None

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
                percent = int(progress * 100)
                self._safe_ui_update(lambda: self.progress_bar.set_value(progress))
                self._safe_ui_update(lambda p=percent: self.progress_label.set_text(f"{p}%"))
                self._safe_ui_update(
                    lambda: self.status_label.set_text(f"Translating block {completed}/{total}...")
                )
        except RuntimeError as e:
            # Handle client disconnection - parent slot deleted
            if "deleted" in str(e).lower():
                logger.debug(f"Timer callback skipped - client disconnected: {e}")
            else:
                raise

    def _change_workflow_mode(self, e):
        """Handle workflow mode change."""
        self.workflow_mode = e.value
        self._rebuild_workflow_sections()
        self._update_action_button()
        self._update_mode_description()
        self._update_idle_instructions()

    def _rebuild_workflow_sections(self):
        """Show/hide sections based on workflow mode."""
        is_scan_copy = self.workflow_mode == "scan_copy"
        is_convert = self.workflow_mode == "convert"
        is_translate = self.workflow_mode == "translate"

        # Update section visibility
        if self.scan_copy_section:
            self.scan_copy_section.set_visibility(is_scan_copy)
        if self.ocr_section:
            self.ocr_section.set_visibility(is_convert or is_translate)
        if self.output_format_section:
            self.output_format_section.set_visibility(is_convert or is_translate)
        if self.translation_settings_section:
            self.translation_settings_section.set_visibility(is_translate)
        if self.translator_section:
            self.translator_section.set_visibility(is_translate)

        # Rebuild output format options based on mode
        self._rebuild_output_format_options()

        # For convert mode, force OCR on and rebuild options
        if is_convert:
            self.use_ocr = True
            self._build_ocr_options()

    def _rebuild_output_format_options(self):
        """Rebuild output format dropdown based on workflow mode."""
        if not self.output_format_select:
            return

        is_convert = self.workflow_mode == "convert"

        if is_convert:
            # Convert mode: only text and markdown
            self.output_format_select.options = OUTPUT_FORMATS_CONVERT
            # If current format is PDF, switch to text
            if self.output_format == "pdf":
                self.output_format = "text"
                self.output_format_select.value = "text"
        else:
            # Translate mode: all formats including PDF
            self.output_format_select.options = OUTPUT_FORMATS
        self.output_format_select.update()

    def _update_action_button(self):
        """Update action button label and icon based on workflow mode."""
        if not self.action_button:
            return

        labels = {
            "scan_copy": ("Create Scanned Copy", "content_copy"),
            "convert": ("Convert", "text_format"),
            "translate": ("Translate", "translate"),
        }
        text, icon = labels[self.workflow_mode]
        self.action_button.text = text
        self.action_button._props["icon"] = icon
        self.action_button.update()

    def _update_mode_description(self):
        """Update mode description text."""
        if not self.mode_description:
            return
        self.mode_description.set_text(WORKFLOW_DESCRIPTIONS[self.workflow_mode])

    def _update_idle_instructions(self):
        """Update idle state instructions based on workflow mode."""
        if not self.idle_instructions:
            return

        self.idle_instructions.clear()
        with self.idle_instructions:
            if self.workflow_mode == "scan_copy":
                ui.label("1. Upload a PDF file").classes("text-sm text-gray-500")
                ui.label("2. Adjust DPI, color, and quality settings").classes(
                    "text-sm text-gray-500"
                )
                ui.label("3. Click Create Scanned Copy").classes("text-sm text-gray-500")
            elif self.workflow_mode == "convert":
                ui.label("1. Upload a PDF file").classes("text-sm text-gray-500")
                ui.label("2. Configure OCR settings").classes("text-sm text-gray-500")
                ui.label("3. Click Convert").classes("text-sm text-gray-500")
            else:  # translate
                ui.label("1. Upload a PDF file").classes("text-sm text-gray-500")
                ui.label("2. Configure translation settings").classes("text-sm text-gray-500")
                ui.label("3. Click Translate").classes("text-sm text-gray-500")

    async def _handle_action(self):
        """Unified action handler based on workflow mode."""
        if self.workflow_mode == "scan_copy":
            await self._create_scanned_copy()
        elif self.workflow_mode == "convert":
            self.use_ocr = True
            self.ocr_only_mode = True
            await self._translate()
        else:  # translate
            self.ocr_only_mode = False
            await self._translate()

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
                    # 1. File upload section (unchanged)
                    with ui.card().classes("w-full"):
                        ui.label("Upload PDF").classes("text-lg font-semibold mb-2")
                        ui.upload(
                            label="Drop PDF here or click to upload",
                            on_upload=self._handle_upload,
                            auto_upload=True,
                            max_file_size=50_000_000,  # 50MB
                        ).props('accept=".pdf"').classes("w-full")

                        self.file_label = ui.label("No file selected").classes(
                            "text-gray-400 text-sm mt-2"
                        )

                    # 2. Workflow Mode Card (NEW)
                    self.workflow_mode_card = ui.card().classes("w-full")
                    with self.workflow_mode_card:
                        ui.label("Workflow Mode").classes("text-lg font-semibold mb-2")
                        ui.radio(
                            options=WORKFLOW_MODES,
                            value=self.workflow_mode,
                            on_change=self._change_workflow_mode,
                        ).props("inline")
                        self.mode_description = ui.label(
                            WORKFLOW_DESCRIPTIONS[self.workflow_mode]
                        ).classes("text-xs text-gray-500 mt-2")

                    # 3. Scanned Copy Section (visible only in scan_copy mode)
                    self.scan_copy_section = ui.card().classes("w-full")
                    self.scan_copy_section.set_visibility(False)
                    with self.scan_copy_section:
                        ui.label("Scan Settings").classes("text-lg font-semibold mb-2")

                        with ui.row().classes("items-center gap-4 flex-wrap"):
                            ui.select(
                                label="DPI",
                                options={
                                    "150": "150 (Fast)",
                                    "300": "300 (Standard)",
                                    "600": "600 (High Quality)",
                                },
                                value="300",
                                on_change=lambda e: setattr(self, "scan_dpi", int(e.value)),
                            ).classes("w-32")

                            ui.select(
                                label="Color Mode",
                                options={
                                    "color": "Color",
                                    "grayscale": "Grayscale",
                                    "bw": "B&W",
                                },
                                value="color",
                                on_change=lambda e: setattr(self, "scan_color_mode", e.value),
                            ).classes("w-28")

                        with ui.row().classes("items-center gap-2 mt-2"):
                            ui.label("Quality:").classes("text-sm")
                            ui.slider(
                                min=1,
                                max=100,
                                value=self.scan_quality,
                                on_change=lambda e: setattr(self, "scan_quality", int(e.value)),
                            ).classes("w-40")
                            ui.label().bind_text_from(
                                self, "scan_quality", lambda v: f"{v}%"
                            ).classes("text-sm w-12")

                        ui.label(
                            "Creates an image-based PDF. Lower quality = smaller file size."
                        ).classes("text-xs text-gray-500 mt-2")

                    # 4. OCR Settings Card (visible in convert and translate modes)
                    self.ocr_section = ui.card().classes("w-full")
                    with self.ocr_section:
                        ui.label("OCR Settings").classes("text-lg font-semibold mb-2")

                        # OCR checkbox only shown in translate mode
                        self.ocr_checkbox_container = ui.column().classes("w-full")
                        with self.ocr_checkbox_container:
                            ui.checkbox(
                                "Use OCR (for scanned/image PDFs)",
                                value=self.use_ocr,
                                on_change=self._toggle_ocr,
                            )

                        self.ocr_options_container = ui.column().classes("w-full gap-2 mt-2")
                        self._build_ocr_options()

                    # 5. Output Format Section (visible in convert and translate modes)
                    self.output_format_section = ui.card().classes("w-full")
                    with self.output_format_section:
                        ui.label("Output Format").classes("text-lg font-semibold mb-2")
                        self.output_format_select = ui.select(
                            label="Format",
                            options=OUTPUT_FORMATS,
                            value=self.output_format,
                            on_change=lambda e: setattr(self, "output_format", e.value),
                        ).classes("w-full")

                    # 6. Translation Settings Card (visible only in translate mode)
                    self.translation_settings_section = ui.card().classes("w-full")
                    with self.translation_settings_section:
                        ui.label("Translation Settings").classes("text-lg font-semibold mb-2")

                        ui.select(
                            label="Target Language",
                            options=TARGET_LANGUAGES,
                            value=self.target_lang,
                            on_change=lambda e: setattr(self, "target_lang", e.value),
                        ).classes("w-full")

                        ui.select(
                            label="Translation Mode",
                            options=TRANSLATION_MODES,
                            value=self.translation_mode,
                            on_change=lambda e: setattr(self, "translation_mode", e.value),
                        ).classes("w-full mt-2")
                        ui.label(
                            "Structure Preserving keeps original layout and scales fonts to fit"
                        ).classes("text-xs text-gray-500")

                    # 7. Translator Card (visible only in translate mode)
                    self.translator_section = ui.card().classes("w-full")
                    with self.translator_section:
                        ui.label("Translator").classes("text-lg font-semibold mb-2")

                        ui.select(
                            label="Translation Backend",
                            options=TRANSLATORS,
                            value=self.translator,
                            on_change=self._change_translator,
                        ).classes("w-full")

                        self.translator_options_container = ui.column().classes("w-full gap-2 mt-2")
                        self._build_translator_options()

                    # 8. Action Button (dynamic label/icon)
                    self.action_button = (
                        ui.button(
                            "Translate",
                            on_click=self._handle_action,
                            icon="translate",
                        )
                        .props("color=primary size=lg")
                        .classes("w-full")
                    )

                # Right column - Status Panel
                with ui.column().classes("gap-4").style("flex: 1 1 400px; min-width: 300px;"):
                    with ui.card().classes("w-full min-h-80"):
                        ui.label("Status").classes("text-lg font-semibold mb-4")

                        # Idle state container
                        self.idle_container = ui.column().classes("w-full items-center gap-2")
                        with self.idle_container:
                            ui.icon("info", size="xl", color="grey")
                            ui.label("Ready to process").classes("text-xl text-gray-400 mt-2")
                            self.idle_instructions = ui.column().classes("mt-4 gap-1")
                            with self.idle_instructions:
                                ui.label("1. Upload a PDF file").classes("text-sm text-gray-500")
                                ui.label("2. Configure translation settings").classes(
                                    "text-sm text-gray-500"
                                )
                                ui.label("3. Click Translate").classes("text-sm text-gray-500")

                        # Progress state container
                        self.progress_container = ui.column().classes("w-full items-center gap-4")
                        self.progress_container.bind_visibility_from(self, "is_translating")
                        with self.progress_container:
                            ui.icon("hourglass_empty", size="xl", color="primary")
                            self.status_label = ui.label("Starting...").classes(
                                "text-lg text-gray-400"
                            )
                            self.progress_bar = ui.linear_progress(value=0).classes("w-full")
                            self.progress_label = ui.label("0%").classes("text-sm text-gray-400")

                        # Timer for polling progress queue (100ms interval for smooth updates)
                        self._progress_timer = ui.timer(
                            0.1, callback=self._poll_progress_updates, active=False
                        )

                        # Complete state container
                        self.complete_container = ui.column().classes("w-full items-center gap-4")
                        self.complete_container.set_visibility(False)
                        with self.complete_container:
                            ui.icon("check_circle", size="xl", color="green")
                            ui.label("Complete!").classes("text-xl text-green-500")
                            self.download_button = (
                                ui.button(
                                    "Download Result",
                                    on_click=self._download_result,
                                    icon="download",
                                )
                                .props("color=positive size=lg")
                                .classes("w-full max-w-xs")
                            )

            # Apply initial workflow mode visibility
            self._rebuild_workflow_sections()

    def _build_ocr_options(self):
        """Build OCR-specific options."""
        self.ocr_options_container.clear()

        # In convert mode, OCR is mandatory - hide checkbox and always show options
        is_convert = self.workflow_mode == "convert"

        if is_convert:
            # Hide the OCR checkbox in convert mode
            self.ocr_checkbox_container.set_visibility(False)
            self.use_ocr = True  # Force OCR on
        else:
            # Show checkbox in translate mode
            self.ocr_checkbox_container.set_visibility(True)

        # Show OCR options if OCR is enabled or in convert mode
        if not self.use_ocr and not is_convert:
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
                    on_change=lambda e: setattr(self, "ocr_dpi", int(e.value))
                    if e.value is not None
                    else None,
                ).classes("flex-1")

    def _toggle_ocr(self, e):
        """Toggle OCR mode."""
        self.use_ocr = e.value
        self._build_ocr_options()
        self.ocr_options_container.update()

    async def _create_scanned_copy(self):
        """Create a scanned copy of the uploaded PDF."""
        if not self.uploaded_file:
            ui.notify("Please upload a PDF file first", type="warning")
            return

        # Show progress state
        self.is_translating = True
        self.action_button.disable()
        self.idle_container.set_visibility(False)
        self.complete_container.set_visibility(False)

        self._safe_ui_update(lambda: self.progress_bar.set_value(0.1))
        self._safe_ui_update(lambda: self.progress_label.set_text("10%"))
        self._safe_ui_update(lambda: self.status_label.set_text("Creating scanned copy..."))

        tmp_input_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_input:
                tmp_input.write(self.uploaded_file)
                tmp_input_path = Path(tmp_input.name)

            from legacylipi.core.output_generator import OutputGenerator

            generator = OutputGenerator()

            self._safe_ui_update(lambda: self.progress_bar.set_value(0.3))
            self._safe_ui_update(lambda: self.progress_label.set_text("30%"))
            self._safe_ui_update(lambda: self.status_label.set_text("Rendering pages as images..."))
            await asyncio.sleep(0.1)  # Allow UI to update

            loop = asyncio.get_event_loop()
            result_bytes = await loop.run_in_executor(
                None,
                lambda: generator.generate_scanned_copy(
                    input_path=tmp_input_path,
                    dpi=self.scan_dpi,
                    color_mode=self.scan_color_mode,
                    quality=self.scan_quality,
                ),
            )

            # Set result for download
            base_name = Path(self.uploaded_filename).stem if self.uploaded_filename else "document"
            self.result_content = result_bytes
            self.result_filename = f"{base_name}_scanned.pdf"

            self._safe_ui_update(lambda: self.progress_bar.set_value(1.0))
            self._safe_ui_update(lambda: self.progress_label.set_text("100%"))
            self._safe_ui_update(lambda: self.status_label.set_text("Complete!"))
            self._safe_ui_update(lambda: self.complete_container.set_visibility(True))
            ui.notify("Scanned copy created successfully!", type="positive")

        except Exception as e:
            logger.exception("Error creating scanned copy")
            self._safe_ui_update(lambda: self.idle_container.set_visibility(True))
            self._safe_ui_update(lambda e=e: self.status_label.set_text(f"Error: {str(e)}"))
            ui.notify(f"Error: {e}", type="negative")
        finally:
            self.is_translating = False
            self._safe_ui_update(lambda: self.action_button.enable())
            if tmp_input_path and tmp_input_path.exists():
                tmp_input_path.unlink()

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

        if self.translator == "openai" and not self.openai_key and not self.ocr_only_mode:
            ui.notify("Please enter your OpenAI API key.", type="warning")
            return

        if self.translator == "gcp_cloud" and not self.gcp_project and not self.ocr_only_mode:
            # Try to get from environment
            import os

            if not os.environ.get("GCP_PROJECT_ID"):
                ui.notify("Please enter your GCP Project ID.", type="warning")
                return

        self.is_translating = True
        self.action_button.disable()
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
            from legacylipi.core.models import (
                DetectionMethod,
                EncodingDetectionResult,
                OutputFormat,
            )
            from legacylipi.core.output_generator import OutputGenerator
            from legacylipi.core.pdf_parser import parse_pdf
            from legacylipi.core.translator import UsageLimitExceededError, create_translator
            from legacylipi.core.unicode_converter import UnicodeConverter

            # Create temp file for input
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(self.uploaded_file)
                input_path = Path(tmp.name)

            try:
                # Step 1: Parse PDF
                self._safe_ui_update(lambda: self.progress_bar.set_value(0.1))
                self._safe_ui_update(lambda: self.progress_label.set_text("10%"))
                self._safe_ui_update(lambda: self.status_label.set_text("Parsing PDF..."))
                await asyncio.sleep(0.1)  # Allow UI to update

                # Get event loop for running blocking operations
                loop = asyncio.get_event_loop()

                if self.use_ocr:
                    # Select OCR engine based on user choice
                    if self.ocr_engine == "easyocr":
                        from legacylipi.core.ocr_parser import parse_pdf_with_easyocr

                        self._safe_ui_update(
                            lambda: self.status_label.set_text(
                                "Running EasyOCR (first run downloads models)..."
                            )
                        )
                        # Run EasyOCR in executor to avoid blocking the event loop
                        document = await loop.run_in_executor(
                            None,
                            lambda: parse_pdf_with_easyocr(
                                input_path, lang=self.ocr_lang, dpi=self.ocr_dpi
                            ),
                        )
                    else:
                        from legacylipi.core.ocr_parser import parse_pdf_with_ocr

                        self._safe_ui_update(
                            lambda: self.status_label.set_text("Running Tesseract OCR...")
                        )
                        # Run Tesseract in executor to avoid blocking the event loop
                        document = await loop.run_in_executor(
                            None,
                            lambda: parse_pdf_with_ocr(
                                input_path, lang=self.ocr_lang, dpi=self.ocr_dpi
                            ),
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
                    self._safe_ui_update(lambda: self.progress_bar.set_value(0.2))
                    self._safe_ui_update(lambda: self.progress_label.set_text("20%"))
                    self._safe_ui_update(
                        lambda: self.status_label.set_text("Detecting encoding...")
                    )
                    await asyncio.sleep(0.1)

                    detector = EncodingDetector()
                    # Run encoding detection in executor
                    encoding_result, page_encodings = await loop.run_in_executor(
                        None, lambda: detector.detect_from_document(document)
                    )

                    # Step 3: Convert to Unicode
                    self._safe_ui_update(lambda: self.progress_bar.set_value(0.3))
                    self._safe_ui_update(lambda: self.progress_label.set_text("30%"))
                    self._safe_ui_update(
                        lambda: self.status_label.set_text("Converting to Unicode...")
                    )
                    await asyncio.sleep(0.1)

                    converter = UnicodeConverter()
                    # Run Unicode conversion in executor
                    converted_doc = await loop.run_in_executor(
                        None,
                        lambda: converter.convert_document(document, page_encodings=page_encodings),
                    )

                # Step 4: Translate (skip if OCR-only mode)
                translation_result = None
                use_structure_preserving = False

                if self.ocr_only_mode:
                    # OCR-only mode: skip translation, output Unicode text directly
                    self._safe_ui_update(lambda: self.progress_bar.set_value(0.7))
                    self._safe_ui_update(lambda: self.progress_label.set_text("70%"))
                    self._safe_ui_update(
                        lambda: self.status_label.set_text(
                            "Skipping translation (OCR-only mode)..."
                        )
                    )
                    logger.info("OCR-only mode: skipping translation step")
                    await asyncio.sleep(0.1)
                else:
                    # Normal translation flow
                    self._safe_ui_update(lambda: self.progress_bar.set_value(0.4))
                    self._safe_ui_update(lambda: self.progress_label.set_text("40%"))
                    self._safe_ui_update(
                        lambda: self.status_label.set_text(f"Translating with {self.translator}...")
                    )
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
                            logger.info(
                                f"Structure-preserving mode: {total_blocks} blocks to translate"
                            )
                            self._safe_ui_update(
                                lambda: self.status_label.set_text(
                                    f"Translating {total_blocks} text blocks..."
                                )
                            )

                            # Progress callback for block translation
                            def update_progress(completed: int, total: int):
                                progress = 0.4 + (0.4 * completed / total)
                                if completed % 50 == 0 or completed == total:
                                    logger.info(
                                        f"Translation progress: {completed}/{total} blocks "
                                        f"({progress * 100:.1f}%)"
                                    )
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
                                translated_count = sum(
                                    1
                                    for b in all_blocks
                                    if b.translated_text
                                    and b.translated_text != (b.unicode_text or b.raw_text)
                                )
                                if translated_count == 0:
                                    self._safe_ui_update(
                                        lambda: ui.notify(
                                            "Warning: No blocks were translated. "
                                            "Check API key and model.",
                                            type="warning",
                                        )
                                    )
                            except UsageLimitExceededError as e:
                                self._safe_ui_update(
                                    lambda e=e: ui.notify(
                                        f"GCP free tier limit exceeded: "
                                        f"{e.current_usage:,}/{e.limit:,} chars. "
                                        f"Need {e.requested:,} more. Try a different translator.",
                                        type="warning",
                                        timeout=10000,
                                    )
                                )
                                raise
                            except Exception as e:
                                self._safe_ui_update(
                                    lambda e=e: ui.notify(
                                        f"Translation error: {e}", type="negative"
                                    )
                                )
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
                                lambda: engine.translate(
                                    unicode_text, source_lang="mr", target_lang=self.target_lang
                                ),
                            )
                            if not translation_result or not translation_result.translated_text:
                                self._safe_ui_update(
                                    lambda: ui.notify(
                                        "Warning: Translation returned empty result. "
                                        "Check API key and model.",
                                        type="warning",
                                    )
                                )
                        except UsageLimitExceededError as e:
                            self._safe_ui_update(
                                lambda e=e: ui.notify(
                                    f"GCP free tier limit exceeded: "
                                    f"{e.current_usage:,}/{e.limit:,} chars. "
                                    f"Need {e.requested:,} more. Try a different translator.",
                                    type="warning",
                                    timeout=10000,
                                )
                            )
                            raise
                        except Exception as e:
                            self._safe_ui_update(
                                lambda e=e: ui.notify(f"Translation error: {e}", type="negative")
                            )
                            raise

                self._safe_ui_update(lambda: self.progress_bar.set_value(0.8))
                self._safe_ui_update(lambda: self.progress_label.set_text("80%"))
                self._safe_ui_update(lambda: self.status_label.set_text("Generating output..."))
                await asyncio.sleep(0.1)

                # Step 5: Generate output
                fmt_map = {
                    "pdf": OutputFormat.PDF,
                    "text": OutputFormat.TEXT,
                    "markdown": OutputFormat.MARKDOWN,
                }
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
                # Use "_converted" suffix for OCR-only mode, "_translated" otherwise
                suffix = "_converted" if self.ocr_only_mode else "_translated"
                self.result_filename = f"{base_name}{suffix}{ext}"

                self._safe_ui_update(lambda: self.progress_bar.set_value(1.0))
                self._safe_ui_update(lambda: self.progress_label.set_text("100%"))
                self._safe_ui_update(lambda: self.status_label.set_text("Complete!"))

                action = "Conversion" if self.ocr_only_mode else "Translation"
                logger.info(
                    f"{action} completed successfully: output={self.result_filename}, "
                    f"size={len(self.result_content)} bytes"
                )

                self._safe_ui_update(
                    lambda a=action: ui.notify(f"{a} completed successfully!", type="positive")
                )
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
                },
            )
            self._safe_ui_update(
                lambda e=e: ui.notify(f"Translation failed: {str(e)}", type="negative")
            )
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
            self._safe_ui_update(lambda: self.action_button.enable())

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
