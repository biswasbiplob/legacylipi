# LegacyLipi - Project Context

## Project Overview
LegacyLipi is a PDF translator for legacy Indian font encodings (Marathi, Hindi, Tamil, etc.). It converts PDFs with legacy encodings to Unicode and translates them to various target languages.

## Project Structure
```
legacylipi/
├── src/legacylipi/
│   ├── core/                    # Core translation pipeline
│   │   ├── models.py            # Data models (TextBlock, PDFPage, PDFDocument, etc.)
│   │   ├── pdf_parser.py        # PDF text extraction with PyMuPDF
│   │   ├── ocr_parser.py        # OCR extraction with Tesseract
│   │   ├── encoding_detector.py # Legacy encoding detection
│   │   ├── unicode_converter.py # Legacy to Unicode conversion
│   │   ├── translator.py        # Translation backends (Google, Ollama, OpenAI, etc.)
│   │   └── output_generator.py  # Output generation (PDF, text, markdown)
│   ├── ui/
│   │   └── app.py               # NiceGUI web interface
│   └── cli.py                   # Command-line interface
```

## Key Data Models (models.py)

### TextBlock
- `raw_text`: Original extracted text
- `unicode_text`: Converted Unicode text
- `translated_text`: Block-level translation (for structure-preserving mode)
- `position`: BoundingBox with x0, y0, x1, y1 coordinates
- `font_name`, `font_size`: Font information

### PDFPage
- `page_number`: 1-indexed page number
- `text_blocks`: List of TextBlock objects
- `width`, `height`: Page dimensions in points

### PDFDocument
- `filepath`: Source PDF path
- `pages`: List of PDFPage objects
- `fonts`: List of FontInfo objects

## Translation Pipeline

1. **Parse PDF**: Extract text with `pdf_parser.py` or `ocr_parser.py` (for scanned docs)
2. **Detect Encoding**: Identify legacy encoding with `encoding_detector.py`
3. **Convert to Unicode**: Transform legacy text with `unicode_converter.py`
4. **Translate**: Use translation backend via `translator.py`
5. **Generate Output**: Create PDF/text/markdown with `output_generator.py`

## Translation Modes

### Flowing Text Mode
- Combines all text into one string with page markers (`--- Page N ---`)
- Translates as single request
- Text flows onto pages in standard A4 layout
- Use when: text output, markdown output, or no position data

### Structure Preserving Mode
- Translates each TextBlock individually
- Preserves original bounding box positions
- Scales font down to fit translated text in original bounds
- Use when: PDF output with OCR (has position data)

## Translation Backends (translator.py)

| Backend | Class | Notes |
|---------|-------|-------|
| `google` | `GoogleTranslateBackend` | Free web API, rate limited |
| `mymemory` | `MyMemoryTranslationBackend` | Free, 500 char limit per request |
| `trans` | `TranslateShellBackend` | CLI tool, requires `translate-shell` |
| `ollama` | `OllamaTranslationBackend` | Local LLM, requires Ollama server |
| `openai` | `OpenAITranslationBackend` | Requires API key |
| `mock` | `MockTranslationBackend` | For testing |

## Key Methods

### TranslationEngine
- `translate(text, source_lang, target_lang)` - Sync translation
- `translate_async(...)` - Async translation
- `translate_blocks_async(blocks, ..., max_concurrent=3)` - Block-level translation with rate limiting

### OutputGenerator
- `generate(document, encoding_result, translation_result, format)` - Main entry point
- `generate_pdf(..., structure_preserving_translation=True)` - Structure-preserving PDF
- `_calculate_block_font_size(text, width, height, original_size)` - Font scaling
- `_place_translated_blocks_with_positions(page, blocks, font_path)` - Block rendering

## UI (app.py)

- Framework: NiceGUI
- Port: 8080
- Key state variables:
  - `translation_mode`: "structure_preserving" or "flowing"
  - `output_format`: "pdf", "text", or "markdown"
  - `use_ocr`: Enable OCR for scanned PDFs
  - `translator`: Backend selection

## Running the Application

```bash
cd legacylipi
uv run python -m legacylipi.ui.app    # Web UI
uv run python -m legacylipi.cli       # CLI
```

## Dependencies

- `pymupdf` (fitz): PDF parsing and generation
- `pytesseract`: OCR extraction
- `nicegui`: Web UI framework
- `httpx`: Async HTTP client for translation APIs

## Font Handling

Unicode fonts searched in order:
1. Noto Sans Devanagari (Linux)
2. FreeSerif/FreeSans (Linux)
3. DevanagariMT/Kohinoor (macOS)
4. Mangal/NirmalaUI (Windows)

## OCR Languages (Tesseract codes)

| Code | Language |
|------|----------|
| `mar` | Marathi |
| `hin` | Hindi |
| `tam` | Tamil |
| `tel` | Telugu |
| `kan` | Kannada |
| `mal` | Malayalam |
| `ben` | Bengali |
| `guj` | Gujarati |
| `pan` | Punjabi |
| `san` | Sanskrit |
