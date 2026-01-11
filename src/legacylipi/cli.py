"""Command Line Interface for LegacyLipi.

This module provides the CLI commands for the LegacyLipi tool.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from legacylipi.core.encoding_detector import EncodingDetector, detect_encoding
from legacylipi.core.models import OutputFormat
from legacylipi.core.ocr_parser import (
    OCRError,
    OCRParser,
    TesseractNotFoundError,
    check_language_available,
    check_tesseract_available,
    get_available_languages,
    parse_pdf_with_ocr,
)
from legacylipi.core.output_generator import OutputGenerator
from legacylipi.core.pdf_parser import PDFParseError, parse_pdf
from legacylipi.core.translator import TranslationEngine, TranslationError, create_translator
from legacylipi.core.unicode_converter import UnicodeConverter
from legacylipi.mappings.loader import MappingLoader

# Initialize Rich console
console = Console()


def print_banner():
    """Print the LegacyLipi banner."""
    console.print("\n[bold blue]LegacyLipi[/bold blue] v0.1.0", style="bold")
    console.print("[dim]Legacy Font PDF Translator[/dim]")
    console.print("─" * 50)


def print_error(message: str):
    """Print an error message."""
    console.print(f"\n[bold red]❌ Error:[/bold red] {message}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"\n[bold green]✓[/bold green] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


@click.group()
@click.version_option(version="0.1.0", prog_name="LegacyLipi")
def main():
    """LegacyLipi - Legacy Font PDF Translator.

    Translate PDF documents with legacy Indian font encodings to English.
    """
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    help="Output file path. Defaults to input file with new extension.",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "markdown", "md", "pdf"]),
    default="text",
    help="Output format (text, markdown, or pdf).",
)
@click.option(
    "--encoding",
    type=str,
    default=None,
    help="Force specific encoding (e.g., shree-lipi, kruti-dev).",
)
@click.option(
    "--target-lang",
    type=str,
    default="en",
    help="Target language code (default: en for English).",
)
@click.option(
    "--translator",
    type=click.Choice(["mock", "google", "trans", "mymemory", "ollama", "openai"]),
    default="google",
    help="Translation backend: google, trans, mymemory, ollama (local LLM), openai (requires OPENAI_API_KEY).",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="Model to use for Ollama backend.",
)
@click.option(
    "--trans-path",
    type=str,
    default=None,
    help="Path to trans executable (for --translator trans). Default: searches PATH and ./trans",
)
@click.option(
    "--no-translate",
    is_flag=True,
    help="Skip translation, only convert to Unicode.",
)
@click.option(
    "--use-ocr",
    is_flag=True,
    help="Use OCR to extract text from PDF (useful for scanned documents or legacy fonts).",
)
@click.option(
    "--ocr-lang",
    type=str,
    default="mar",
    help="OCR language code (e.g., 'mar' for Marathi, 'hin' for Hindi). Default: mar",
)
@click.option(
    "--ocr-dpi",
    type=int,
    default=300,
    help="DPI for OCR rendering (higher = better quality but slower). Default: 300",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress progress output.",
)
def translate(
    input_file: Path,
    output: Optional[Path],
    output_format: str,
    encoding: Optional[str],
    target_lang: str,
    translator: str,
    model: Optional[str],
    trans_path: Optional[str],
    no_translate: bool,
    use_ocr: bool,
    ocr_lang: str,
    ocr_dpi: int,
    quiet: bool,
):
    """Translate a PDF with legacy fonts to Unicode/English.

    This command performs the full translation pipeline:
    1. Parse PDF and extract text (or use OCR with --use-ocr)
    2. Detect font encoding (skipped in OCR mode)
    3. Convert legacy encoding to Unicode (skipped in OCR mode)
    4. Translate to target language
    5. Output to specified format
    """
    if not quiet:
        print_banner()

    # Validate OCR requirements if using OCR mode
    if use_ocr:
        available, msg = check_tesseract_available()
        if not available:
            print_error(msg)
            console.print("\n[dim]To install Tesseract on Ubuntu/Debian:[/dim]")
            console.print("  sudo apt-get install tesseract-ocr tesseract-ocr-mar")
            console.print("\n[dim]On macOS:[/dim]")
            console.print("  brew install tesseract tesseract-lang")
            sys.exit(1)

        if not check_language_available(ocr_lang):
            print_error(f"OCR language '{ocr_lang}' is not available.")
            available_langs = get_available_languages()
            if available_langs:
                console.print(f"\n[dim]Available languages:[/dim] {', '.join(available_langs[:10])}")
            console.print(f"\n[dim]To install Marathi language pack:[/dim]")
            console.print("  sudo apt-get install tesseract-ocr-mar")
            sys.exit(1)

    # Determine output format
    if output_format == "pdf":
        fmt = OutputFormat.PDF
        default_ext = ".pdf"
    elif output_format in ("markdown", "md"):
        fmt = OutputFormat.MARKDOWN
        default_ext = ".md"
    else:
        fmt = OutputFormat.TEXT
        default_ext = ".txt"

    # Determine output path
    if output is None:
        output = input_file.with_suffix(default_ext)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            # Step 1: Parse PDF (with OCR or standard text extraction)
            if use_ocr:
                task = progress.add_task(f"Running OCR ({ocr_lang})...", total=None)
                document = parse_pdf_with_ocr(input_file, lang=ocr_lang, dpi=ocr_dpi)
                progress.update(task, description=f"[green]✓[/green] OCR extracted {document.page_count} pages")

                if not quiet:
                    console.print(f"\n[dim]📄 Input:[/dim] {input_file.name} ({document.page_count} pages)")
                    console.print(f"[dim]👁 OCR:[/dim] {ocr_lang} @ {ocr_dpi} DPI")

                # In OCR mode, text is already Unicode - create dummy encoding result
                from legacylipi.core.models import DetectionMethod, EncodingDetectionResult
                encoding_result = EncodingDetectionResult(
                    detected_encoding="unicode-ocr",
                    confidence=1.0,
                    method=DetectionMethod.UNICODE_DETECTED,
                )
                # OCR output is already Unicode, no conversion needed
                converted_doc = document
            else:
                task = progress.add_task("Parsing PDF...", total=None)
                document = parse_pdf(input_file)
                progress.update(task, description=f"[green]✓[/green] Parsed {document.page_count} pages")

                if not quiet:
                    console.print(f"\n[dim]📄 Input:[/dim] {input_file.name} ({document.page_count} pages)")

                # Step 2: Detect encoding
                progress.update(task, description="Detecting encoding...")
                detector = EncodingDetector()

                if encoding:
                    # User specified encoding
                    from legacylipi.core.models import DetectionMethod, EncodingDetectionResult
                    encoding_result = EncodingDetectionResult(
                        detected_encoding=encoding,
                        confidence=1.0,
                        method=DetectionMethod.USER_OVERRIDE,
                    )
                    page_encodings = {page.page_number: encoding_result for page in document.pages}
                else:
                    encoding_result, page_encodings = detector.detect_from_document(document)

                progress.update(
                    task,
                    description=f"[green]✓[/green] Encoding: {encoding_result.detected_encoding} ({encoding_result.confidence:.0%})"
                )

                if not quiet:
                    console.print(f"[dim]🎯 Encoding:[/dim] {encoding_result.detected_encoding} (confidence: {encoding_result.confidence:.0%})")

                # Step 3: Convert to Unicode
                progress.update(task, description="Converting to Unicode...")
                converter = UnicodeConverter()
                converted_doc = converter.convert_document(
                    document,
                    page_encodings=page_encodings,
                )
                progress.update(task, description="[green]✓[/green] Converted to Unicode")

            # Step 4: Translate (if enabled)
            translation_result = None
            if not no_translate:
                progress.update(task, description=f"Translating with {translator}...")

                translator_kwargs = {}
                if model and translator in ("ollama", "openai"):
                    translator_kwargs["model"] = model
                if trans_path and translator == "trans":
                    translator_kwargs["trans_path"] = trans_path

                engine = create_translator(translator, **translator_kwargs)

                # Build text with page markers for page-by-page output preservation
                # Format: "--- Page N ---\n<page text>\n\n--- Page N+1 ---\n..."
                text_parts = []
                for i, page in enumerate(converted_doc.pages, 1):
                    page_text = page.unicode_text
                    text_parts.append(f"--- Page {i} ---\n{page_text}")
                unicode_text = "\n\n".join(text_parts)

                translation_result = engine.translate(
                    unicode_text,
                    source_lang="mr",
                    target_lang=target_lang,
                )

                # Check if translation actually happened (warnings indicate failures)
                if translation_result.warnings:
                    # Check if ALL chunks failed (no translation happened)
                    if len(translation_result.warnings) >= translation_result.chunk_count:
                        progress.update(
                            task,
                            description=f"[red]✗[/red] Translation failed"
                        )
                        raise TranslationError(
                            f"All translation chunks failed. First error: {translation_result.warnings[0]}"
                        )
                    else:
                        # Partial failure - show warnings
                        progress.update(
                            task,
                            description=f"[yellow]⚠[/yellow] Translated with {len(translation_result.warnings)} warnings"
                        )
                        if not quiet:
                            for warning in translation_result.warnings[:3]:  # Show first 3 warnings
                                console.print(f"[yellow]   ⚠ {warning}[/yellow]")
                            if len(translation_result.warnings) > 3:
                                console.print(f"[yellow]   ... and {len(translation_result.warnings) - 3} more warnings[/yellow]")
                else:
                    progress.update(
                        task,
                        description=f"[green]✓[/green] Translated ({translation_result.chunk_count} chunks)"
                    )

                if not quiet:
                    console.print(f"[dim]🌐 Translated:[/dim] {len(unicode_text)} chars → {target_lang}")

            # Step 5: Generate output
            progress.update(task, description="Generating output...")
            generator = OutputGenerator()
            output_content = generator.generate(
                converted_doc,
                encoding_result,
                translation_result,
                fmt,
            )

            # Save output
            generator.save(output_content, output)
            progress.update(task, description=f"[green]✓[/green] Saved to {output.name}")

        print_success(f"Output saved to: {output}")

        # Print summary if not quiet
        if not quiet:
            console.print("\n[bold]📊 Summary:[/bold]")
            console.print(f"   • Pages processed: {document.page_count}")
            console.print(f"   • Encoding: {encoding_result.detected_encoding}")
            if translation_result:
                console.print(f"   • Translation: {translation_result.source_language} → {translation_result.target_language}")
                console.print(f"   • Backend: {translation_result.translation_backend.value}")

    except PDFParseError as e:
        print_error(f"Failed to parse PDF: {e}")
        sys.exit(1)
    except OCRError as e:
        print_error(f"OCR failed: {e}")
        console.print("\n[dim]Suggestions:[/dim]")
        console.print("  • Ensure Tesseract is installed: sudo apt-get install tesseract-ocr")
        console.print("  • Install language pack: sudo apt-get install tesseract-ocr-mar")
        console.print("  • Try without OCR to use font-based extraction")
        sys.exit(1)
    except TranslationError as e:
        print_error(f"Translation failed: {e}")
        console.print("\n[dim]Suggestions:[/dim]")
        console.print("  • Try [cyan]--translator trans[/cyan] for translate-shell CLI (apt install translate-shell)")
        console.print("  • Try [cyan]--translator ollama[/cyan] for local LLM translation")
        console.print("  • Try [cyan]--translator mymemory[/cyan] for free MyMemory API")
        console.print("  • Try [cyan]--no-translate[/cyan] to skip translation and output Unicode only")
        sys.exit(1)
    except Exception as e:
        # Handle tenacity retry errors that wrap TranslationError
        error_msg = str(e)
        if "TranslationError" in error_msg or "403" in error_msg or "429" in error_msg or "proxy" in error_msg.lower():
            print_error("Translation service unavailable (network may be blocking external APIs)")
            console.print("\n[dim]Suggestions:[/dim]")
            console.print("  • Try [cyan]--translator trans[/cyan] for translate-shell CLI (apt install translate-shell)")
            console.print("  • Try [cyan]--translator ollama[/cyan] for local LLM translation")
            console.print("  • Try [cyan]--translator mymemory[/cyan] for free MyMemory API")
            console.print("  • Try [cyan]--no-translate[/cyan] to skip translation and output Unicode only")
        else:
            print_error(str(e))
            if not quiet:
                console.print_exception()
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    help="Output file path for Unicode text.",
)
@click.option(
    "--encoding",
    type=str,
    default=None,
    help="Force specific encoding.",
)
def convert(
    input_file: Path,
    output: Optional[Path],
    encoding: Optional[str],
):
    """Convert PDF from legacy encoding to Unicode (no translation).

    This command only performs encoding detection and Unicode conversion,
    without translating to another language.
    """
    print_banner()

    if output is None:
        output = input_file.with_suffix(".unicode.txt")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=None)

            # Parse PDF
            document = parse_pdf(input_file)
            progress.update(task, description=f"Parsed {document.page_count} pages")

            # Detect encoding
            detector = EncodingDetector()
            if encoding:
                from legacylipi.core.models import DetectionMethod, EncodingDetectionResult
                encoding_result = EncodingDetectionResult(
                    detected_encoding=encoding,
                    confidence=1.0,
                    method=DetectionMethod.USER_OVERRIDE,
                )
                page_encodings = {page.page_number: encoding_result for page in document.pages}
            else:
                encoding_result, page_encodings = detector.detect_from_document(document)

            progress.update(task, description=f"Encoding: {encoding_result.detected_encoding}")

            # Convert to Unicode
            converter = UnicodeConverter()
            converted_doc = converter.convert_document(document, page_encodings=page_encodings)

            # Output
            generator = OutputGenerator(include_metadata=True)
            content = generator.generate(
                converted_doc,
                encoding_result,
                output_format=OutputFormat.TEXT,
            )
            generator.save(content, output)

        print_success(f"Unicode output saved to: {output}")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    help="Output file path. Defaults to input file with new extension.",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "markdown", "md", "pdf"]),
    default="text",
    help="Output format (text, markdown, or pdf).",
)
@click.option(
    "--encoding",
    type=str,
    default=None,
    help="Force specific encoding (e.g., shree-lipi, kruti-dev).",
)
@click.option(
    "--use-ocr",
    is_flag=True,
    help="Use OCR to extract text from PDF (useful for scanned documents).",
)
@click.option(
    "--ocr-lang",
    type=str,
    default="mar",
    help="OCR language code (e.g., 'mar' for Marathi, 'hin' for Hindi). Default: mar",
)
@click.option(
    "--ocr-dpi",
    type=int,
    default=300,
    help="DPI for OCR rendering (higher = better quality but slower). Default: 300",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress progress output.",
)
def extract(
    input_file: Path,
    output: Optional[Path],
    output_format: str,
    encoding: Optional[str],
    use_ocr: bool,
    ocr_lang: str,
    ocr_dpi: int,
    quiet: bool,
):
    """Extract text from PDF (OCR or font-based) without translation.

    This command extracts text from PDFs using either:
    - OCR mode (--use-ocr): Uses Tesseract to recognize text in scanned documents
    - Font-based mode (default): Extracts embedded text and converts legacy encodings to Unicode

    Examples:
        # Extract with OCR (Marathi)
        legacylipi extract input.pdf --use-ocr -o marathi.txt

        # Extract with OCR (Hindi) at higher quality
        legacylipi extract input.pdf --use-ocr --ocr-lang hin --ocr-dpi 600 -o output.txt

        # Extract with font-based extraction (auto-detect encoding)
        legacylipi extract input.pdf -o output.txt

        # Extract to PDF format (preserves structure)
        legacylipi extract input.pdf --use-ocr -o output.pdf --format pdf
    """
    if not quiet:
        print_banner()

    # Validate OCR requirements if using OCR mode
    if use_ocr:
        available, msg = check_tesseract_available()
        if not available:
            print_error(msg)
            console.print("\n[dim]To install Tesseract on Ubuntu/Debian:[/dim]")
            console.print("  sudo apt-get install tesseract-ocr tesseract-ocr-mar")
            console.print("\n[dim]On macOS:[/dim]")
            console.print("  brew install tesseract tesseract-lang")
            sys.exit(1)

        if not check_language_available(ocr_lang):
            print_error(f"OCR language '{ocr_lang}' is not available.")
            available_langs = get_available_languages()
            if available_langs:
                console.print(f"\n[dim]Available languages:[/dim] {', '.join(available_langs[:10])}")
            console.print(f"\n[dim]To install Marathi language pack:[/dim]")
            console.print("  sudo apt-get install tesseract-ocr-mar")
            sys.exit(1)

    # Determine output format
    if output_format == "pdf":
        fmt = OutputFormat.PDF
        default_ext = ".pdf"
    elif output_format in ("markdown", "md"):
        fmt = OutputFormat.MARKDOWN
        default_ext = ".md"
    else:
        fmt = OutputFormat.TEXT
        default_ext = ".txt"

    # Determine output path
    if output is None:
        suffix = ".extracted" + default_ext
        output = input_file.with_suffix(suffix)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            # Extract text (with OCR or standard text extraction)
            if use_ocr:
                task = progress.add_task(f"Running OCR ({ocr_lang})...", total=None)
                document = parse_pdf_with_ocr(input_file, lang=ocr_lang, dpi=ocr_dpi)
                progress.update(task, description=f"[green]✓[/green] OCR extracted {document.page_count} pages")

                if not quiet:
                    console.print(f"\n[dim]📄 Input:[/dim] {input_file.name} ({document.page_count} pages)")
                    console.print(f"[dim]👁 OCR:[/dim] {ocr_lang} @ {ocr_dpi} DPI")

                # In OCR mode, text is already Unicode
                from legacylipi.core.models import DetectionMethod, EncodingDetectionResult
                encoding_result = EncodingDetectionResult(
                    detected_encoding="unicode-ocr",
                    confidence=1.0,
                    method=DetectionMethod.UNICODE_DETECTED,
                )
                converted_doc = document
            else:
                task = progress.add_task("Parsing PDF...", total=None)
                document = parse_pdf(input_file)
                progress.update(task, description=f"[green]✓[/green] Parsed {document.page_count} pages")

                if not quiet:
                    console.print(f"\n[dim]📄 Input:[/dim] {input_file.name} ({document.page_count} pages)")

                # Detect encoding
                progress.update(task, description="Detecting encoding...")
                detector = EncodingDetector()

                if encoding:
                    from legacylipi.core.models import DetectionMethod, EncodingDetectionResult
                    encoding_result = EncodingDetectionResult(
                        detected_encoding=encoding,
                        confidence=1.0,
                        method=DetectionMethod.USER_OVERRIDE,
                    )
                    page_encodings = {page.page_number: encoding_result for page in document.pages}
                else:
                    encoding_result, page_encodings = detector.detect_from_document(document)

                progress.update(
                    task,
                    description=f"[green]✓[/green] Encoding: {encoding_result.detected_encoding} ({encoding_result.confidence:.0%})"
                )

                if not quiet:
                    console.print(f"[dim]🎯 Encoding:[/dim] {encoding_result.detected_encoding} (confidence: {encoding_result.confidence:.0%})")

                # Convert to Unicode
                progress.update(task, description="Converting to Unicode...")
                converter = UnicodeConverter()
                converted_doc = converter.convert_document(
                    document,
                    page_encodings=page_encodings,
                )
                progress.update(task, description="[green]✓[/green] Converted to Unicode")

            # Generate output (no translation)
            progress.update(task, description="Generating output...")
            generator = OutputGenerator()
            output_content = generator.generate(
                converted_doc,
                encoding_result,
                translation_result=None,  # No translation
                output_format=fmt,
            )

            # Save output
            generator.save(output_content, output)
            progress.update(task, description=f"[green]✓[/green] Saved to {output.name}")

        print_success(f"Output saved to: {output}")

        # Print summary if not quiet
        if not quiet:
            console.print("\n[bold]📊 Summary:[/bold]")
            console.print(f"   • Pages processed: {document.page_count}")
            console.print(f"   • Extraction method: {'OCR' if use_ocr else 'Font-based'}")
            if not use_ocr:
                console.print(f"   • Encoding: {encoding_result.detected_encoding}")
            console.print(f"   • Output format: {output_format}")

    except PDFParseError as e:
        print_error(f"Failed to parse PDF: {e}")
        sys.exit(1)
    except OCRError as e:
        print_error(f"OCR failed: {e}")
        console.print("\n[dim]Suggestions:[/dim]")
        console.print("  • Ensure Tesseract is installed: sudo apt-get install tesseract-ocr")
        console.print("  • Install language pack: sudo apt-get install tesseract-ocr-mar")
        console.print("  • Try without --use-ocr to use font-based extraction")
        sys.exit(1)
    except Exception as e:
        print_error(str(e))
        if not quiet:
            console.print_exception()
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed page-by-page analysis.",
)
def detect(input_file: Path, verbose: bool):
    """Detect the font encoding used in a PDF.

    Analyzes the PDF to identify whether it uses legacy font encoding
    and which specific encoding family it belongs to.
    """
    print_banner()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing...", total=None)

            # Parse PDF
            document = parse_pdf(input_file)
            progress.update(task, description=f"Parsed {document.page_count} pages")

            # Detect encoding
            detector = EncodingDetector()
            encoding_result, page_encodings = detector.detect_from_document(document)

        # Display results
        console.print(f"\n[bold]📄 File:[/bold] {input_file.name}")
        console.print(f"[bold]📊 Pages:[/bold] {document.page_count}")

        # Overall result
        console.print(f"\n[bold]🎯 Detected Encoding:[/bold]")
        console.print(f"   Encoding: [cyan]{encoding_result.detected_encoding}[/cyan]")
        console.print(f"   Confidence: [{'green' if encoding_result.confidence > 0.8 else 'yellow'}]{encoding_result.confidence:.1%}[/]")
        console.print(f"   Method: {encoding_result.method.value}")

        if encoding_result.is_unicode:
            console.print("\n[green]✓ Document is already in Unicode format.[/green]")
        elif encoding_result.is_legacy:
            console.print(f"\n[yellow]⚠ Legacy encoding detected.[/yellow]")
            console.print(f"   Use: [dim]legacylipi translate {input_file.name}[/dim]")

        # Page-by-page analysis if verbose
        if verbose and page_encodings:
            console.print("\n[bold]Page-by-Page Analysis:[/bold]")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Page", justify="right")
            table.add_column("Encoding")
            table.add_column("Confidence", justify="right")
            table.add_column("Method")

            for page_num, result in sorted(page_encodings.items()):
                conf_style = "green" if result.confidence > 0.8 else "yellow"
                table.add_row(
                    str(page_num),
                    result.detected_encoding,
                    f"[{conf_style}]{result.confidence:.0%}[/]",
                    result.method.value,
                )

            console.print(table)

        # Fonts found
        if document.fonts:
            console.print("\n[bold]Fonts Found:[/bold]")
            for font in document.fonts[:10]:  # Limit to first 10
                console.print(f"   • {font.name}")
            if len(document.fonts) > 10:
                console.print(f"   [dim]... and {len(document.fonts) - 10} more[/dim]")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@main.command("encodings")
@click.option(
    "--search", "-s",
    type=str,
    default=None,
    help="Search for encoding by name.",
)
def list_encodings(search: Optional[str]):
    """List supported font encodings.

    Shows all font encoding families that LegacyLipi can detect and convert.
    """
    print_banner()

    loader = MappingLoader()
    encodings = loader.list_available()

    if search:
        encodings = [e for e in encodings if search.lower() in e.lower()]

    console.print(f"\n[bold]Supported Encodings ({len(encodings)}):[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Encoding Name")
    table.add_column("Font Family")
    table.add_column("Language")
    table.add_column("Type")

    from legacylipi.mappings.loader import BUILTIN_MAPPINGS

    for encoding in encodings:
        if encoding in BUILTIN_MAPPINGS:
            mapping = BUILTIN_MAPPINGS[encoding]
            table.add_row(
                encoding,
                mapping.font_family,
                mapping.language,
                "[green]Built-in[/green]",
            )
        else:
            table.add_row(
                encoding,
                "-",
                "-",
                "[dim]External[/dim]",
            )

    console.print(table)

    console.print("\n[dim]Use --encoding <name> with translate/convert commands[/dim]")


if __name__ == "__main__":
    main()
