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

## Automated Testing with Playwright MCP

Use Playwright MCP tools to automate UI testing after code changes.

### Test Workflow

1. **Start the server** (if not running):
   ```bash
   uv run python -m legacylipi.ui.app &
   ```

2. **Navigate to UI**:
   ```
   mcp__playwright__browser_navigate: http://localhost:8080
   ```

3. **Upload test PDF**:
   ```
   mcp__playwright__browser_click: "Choose File" button
   mcp__playwright__browser_file_upload: ["/path/to/test.pdf"]
   ```

4. **Configure settings**:
   ```
   mcp__playwright__browser_click: "Use OCR" checkbox
   # Verify Structure Preserving mode is selected
   # Verify PDF output format
   ```

5. **Run translation**:
   ```
   mcp__playwright__browser_click: "Translate" button
   mcp__playwright__browser_wait_for: Wait for completion (check for "Download" button)
   ```

6. **Download and verify output**:
   ```
   mcp__playwright__browser_click: "Download" button
   # Read the generated PDF to verify output
   ```

7. **Evaluate output quality** (Critical step):
   - Open translated PDF and source PDF side-by-side
   - Check font consistency: All body text should be uniform 11pt
   - Verify no wildly varying font sizes across pages
   - Check text positioning: Translated text should be at similar positions to source
   - If fonts are inconsistent, check `_place_translated_blocks_with_positions()` in output_generator.py
   - Common issue: Font scaling to fit bounding boxes causes inconsistent sizes

### Key UI Elements (refs may change)

| Element | Description |
|---------|-------------|
| Upload area | Drop zone or "Choose File" button |
| OCR checkbox | "Use OCR (for scanned/image PDFs)" |
| Translation Mode | Combobox: "Structure Preserving" or "Flowing Text" |
| Output Format | Combobox: PDF, Text, Markdown |
| Translate button | Main action button |
| Status area | Shows progress and completion |
| Download button | Appears after successful translation |

### Test PDF Location

Test file: `Marathi-Bhascyacha-vaapar.pdf` (135KB, 11 pages)
