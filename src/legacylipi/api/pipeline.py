"""Async pipeline runner extracted from the NiceGUI app.

Provides standalone async functions for each workflow mode:
- run_scan_copy: Create image-based PDF
- run_convert: OCR + Unicode conversion (no translation)
- run_translate: Full pipeline (parse/OCR → detect → convert → translate → output)
"""

import asyncio
import logging
import os
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from legacylipi.api.schemas import ConvertRequest, ScanCopyRequest, TranslateRequest

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str, str], Awaitable[None]]


async def _report(cb: ProgressCallback | None, percent: int, step: str, message: str):
    """Send a progress update if callback is provided."""
    if cb:
        await cb(percent, step, message)


async def run_scan_copy(
    file_bytes: bytes,
    filename: str,
    config: ScanCopyRequest,
    progress_callback: ProgressCallback | None = None,
) -> tuple[bytes, str]:
    """Create an image-based scanned copy of a PDF.

    Returns (result_bytes, result_filename).
    """
    from legacylipi.core.output_generator import OutputGenerator

    await _report(progress_callback, 10, "scanning", "Creating scanned copy...")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        generator = OutputGenerator()
        await _report(progress_callback, 30, "scanning", "Rendering pages as images...")

        loop = asyncio.get_event_loop()
        result_bytes = await loop.run_in_executor(
            None,
            lambda: generator.generate_scanned_copy(
                input_path=tmp_path,
                dpi=config.dpi,
                color_mode=config.color_mode,
                quality=config.quality,
            ),
        )

        base_name = Path(filename).stem
        result_filename = f"{base_name}_scanned.pdf"

        await _report(progress_callback, 100, "complete", "Scanned copy created!")
        return result_bytes, result_filename
    finally:
        tmp_path.unlink(missing_ok=True)


async def run_convert(
    file_bytes: bytes,
    filename: str,
    config: ConvertRequest,
    progress_callback: ProgressCallback | None = None,
) -> tuple[bytes, str]:
    """Run OCR + Unicode conversion (no translation).

    Returns (result_bytes, result_filename).
    """
    from legacylipi.core.models import DetectionMethod, EncodingDetectionResult, OutputFormat
    from legacylipi.core.output_generator import OutputGenerator

    loop = asyncio.get_event_loop()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        # Step 1: OCR
        await _report(progress_callback, 10, "parsing", "Running OCR...")

        if config.ocr_engine == "easyocr":
            from legacylipi.core.ocr_parser import parse_pdf_with_easyocr

            document = await loop.run_in_executor(
                None,
                lambda: parse_pdf_with_easyocr(tmp_path, lang=config.ocr_lang, dpi=config.ocr_dpi),
            )
        else:
            from legacylipi.core.ocr_parser import parse_pdf_with_ocr

            document = await loop.run_in_executor(
                None,
                lambda: parse_pdf_with_ocr(tmp_path, lang=config.ocr_lang, dpi=config.ocr_dpi),
            )

        encoding_result = EncodingDetectionResult(
            detected_encoding="unicode-ocr",
            confidence=1.0,
            method=DetectionMethod.UNICODE_DETECTED,
        )

        await _report(progress_callback, 70, "generating", "Generating output...")

        # Generate output
        fmt_map = {
            "pdf": OutputFormat.PDF,
            "text": OutputFormat.TEXT,
            "markdown": OutputFormat.MARKDOWN,
        }
        output_fmt = fmt_map.get(config.output_format, OutputFormat.TEXT)

        generator = OutputGenerator()
        output_content = generator.generate(document, encoding_result, None, output_fmt)

        if isinstance(output_content, bytes):
            result_bytes = output_content
        else:
            result_bytes = output_content.encode("utf-8")

        ext_map = {"pdf": ".pdf", "text": ".txt", "markdown": ".md"}
        ext = ext_map.get(config.output_format, ".txt")
        result_filename = f"{Path(filename).stem}_converted{ext}"

        await _report(progress_callback, 100, "complete", "Conversion complete!")
        return result_bytes, result_filename
    finally:
        tmp_path.unlink(missing_ok=True)


async def run_translate(
    file_bytes: bytes,
    filename: str,
    config: TranslateRequest,
    progress_callback: ProgressCallback | None = None,
) -> tuple[bytes, str]:
    """Run the full translation pipeline.

    Returns (result_bytes, result_filename).
    """
    from legacylipi.core.encoding_detector import EncodingDetector
    from legacylipi.core.models import DetectionMethod, EncodingDetectionResult, OutputFormat
    from legacylipi.core.output_generator import OutputGenerator
    from legacylipi.core.pdf_parser import parse_pdf
    from legacylipi.core.translator import create_translator
    from legacylipi.core.unicode_converter import UnicodeConverter

    loop = asyncio.get_event_loop()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        # Step 1: Parse PDF
        await _report(progress_callback, 10, "parsing", "Parsing PDF...")

        if config.use_ocr:
            if config.ocr_engine == "easyocr":
                from legacylipi.core.ocr_parser import parse_pdf_with_easyocr

                await _report(
                    progress_callback,
                    10,
                    "parsing",
                    "Running EasyOCR (first run downloads models)...",
                )
                document = await loop.run_in_executor(
                    None,
                    lambda: parse_pdf_with_easyocr(
                        tmp_path, lang=config.ocr_lang, dpi=config.ocr_dpi
                    ),
                )
            else:
                from legacylipi.core.ocr_parser import parse_pdf_with_ocr

                await _report(progress_callback, 10, "parsing", "Running Tesseract OCR...")
                document = await loop.run_in_executor(
                    None,
                    lambda: parse_pdf_with_ocr(tmp_path, lang=config.ocr_lang, dpi=config.ocr_dpi),
                )

            encoding_result = EncodingDetectionResult(
                detected_encoding="unicode-ocr",
                confidence=1.0,
                method=DetectionMethod.UNICODE_DETECTED,
            )
            converted_doc = document
        else:
            document = await loop.run_in_executor(None, lambda: parse_pdf(tmp_path))

            # Step 2: Detect encoding
            await _report(progress_callback, 20, "detecting", "Detecting encoding...")
            detector = EncodingDetector()
            encoding_result, page_encodings = await loop.run_in_executor(
                None, lambda: detector.detect_from_document(document)
            )

            # Step 3: Convert to Unicode
            await _report(progress_callback, 30, "converting", "Converting to Unicode...")
            converter = UnicodeConverter()
            converted_doc = await loop.run_in_executor(
                None,
                lambda: converter.convert_document(document, page_encodings=page_encodings),
            )

        # Step 4: Translate
        await _report(
            progress_callback, 40, "translating", f"Translating with {config.translator}..."
        )

        translator_kwargs: dict = {}
        if config.translator == "openai" and config.openai_key:
            translator_kwargs["api_key"] = config.openai_key
            translator_kwargs["model"] = config.openai_model
        elif config.translator == "ollama":
            translator_kwargs["model"] = config.ollama_model
            if config.ollama_host:
                translator_kwargs["host"] = config.ollama_host
        elif config.translator == "trans" and config.trans_path:
            translator_kwargs["trans_path"] = config.trans_path
        elif config.translator == "gcp_cloud":
            project_id = config.gcp_project or os.environ.get("GCP_PROJECT_ID")
            if project_id:
                translator_kwargs["project_id"] = project_id

        engine = create_translator(config.translator, **translator_kwargs)

        translation_result = None
        use_structure_preserving = (
            config.translation_mode == "structure_preserving" and config.output_format == "pdf"
        )

        if use_structure_preserving:
            # Translate each block individually
            all_blocks = [
                block
                for page in converted_doc.pages
                for block in page.text_blocks
                if block.position is not None
            ]

            if all_blocks:
                total_blocks = len(all_blocks)
                logger.info(f"Structure-preserving mode: {total_blocks} blocks to translate")

                async def block_progress(completed: int, total: int):
                    percent = 40 + int(40 * completed / total)
                    await _report(
                        progress_callback,
                        percent,
                        "translating",
                        f"Translating block {completed}/{total}...",
                    )

                # Wrap sync callback for translate_blocks_async
                def sync_progress(completed: int, total: int):
                    asyncio.get_event_loop().create_task(block_progress(completed, total))

                await engine.translate_blocks_async(
                    all_blocks,
                    source_lang="mr",
                    target_lang=config.target_lang,
                    max_concurrent=3,
                    progress_callback=sync_progress,
                )
            else:
                use_structure_preserving = False

        if not use_structure_preserving:
            # Flowing mode: combine text and translate as one string
            text_parts = []
            for i, page in enumerate(converted_doc.pages, 1):
                page_text = page.unicode_text
                text_parts.append(f"--- Page {i} ---\n{page_text}")
            unicode_text = "\n\n".join(text_parts)

            translation_result = await loop.run_in_executor(
                None,
                lambda: engine.translate(
                    unicode_text, source_lang="mr", target_lang=config.target_lang
                ),
            )

        # Step 5: Generate output
        await _report(progress_callback, 80, "generating", "Generating output...")

        fmt_map = {
            "pdf": OutputFormat.PDF,
            "text": OutputFormat.TEXT,
            "markdown": OutputFormat.MARKDOWN,
        }
        output_fmt = fmt_map.get(config.output_format, OutputFormat.TEXT)

        generator = OutputGenerator()

        if use_structure_preserving and output_fmt == OutputFormat.PDF:
            output_content = generator.generate_pdf(
                converted_doc,
                encoding_result,
                translation_result=None,
                structure_preserving_translation=True,
            )
        else:
            output_content = generator.generate(
                converted_doc, encoding_result, translation_result, output_fmt
            )

        if isinstance(output_content, bytes):
            result_bytes = output_content
        else:
            result_bytes = output_content.encode("utf-8")

        ext_map = {"pdf": ".pdf", "text": ".txt", "markdown": ".md"}
        ext = ext_map.get(config.output_format, ".txt")
        result_filename = f"{Path(filename).stem}_translated{ext}"

        await _report(progress_callback, 100, "complete", "Translation complete!")
        return result_bytes, result_filename
    finally:
        tmp_path.unlink(missing_ok=True)
