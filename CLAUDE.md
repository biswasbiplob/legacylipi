# LegacyLipi - Project Context

## Project Overview
LegacyLipi is a PDF translator for legacy Indian font encodings (Marathi, Hindi, Tamil, etc.). It converts PDFs with legacy encodings to Unicode and translates them to various target languages.

## Development Guidelines

### Feature Branches
**Always create new features in feature branches** so that we have a PR for everything new.
- Branch naming: `feature/<feature-name>` (e.g., `feature/ocr-only-mode`)
- Create PR after implementation is complete
- Never commit directly to `main` for new features

### Version Bumping
**Always bump the version when adding new features or making significant changes.**

Version is defined in these locations (keep them in sync):
- `pyproject.toml` - line 7 (`version = "x.y.z"`)
- `src/legacylipi/__init__.py` - line 6 (`__version__ = "x.y.z"`)

Follow semantic versioning:
- **MAJOR** (x.0.0): Breaking changes
- **MINOR** (0.x.0): New features (backward compatible)
- **PATCH** (0.0.x): Bug fixes

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

## Supported Legacy Font Encodings

| Encoding | Font Families | Language | Notes |
|----------|---------------|----------|-------|
| `shree-dev` | SHREE-DEV-0708, 0714, 0715, 0721 | Marathi | Primary encoding, comprehensive mapping |
| `shree-lipi` | Shree-Lipi, SDL-DEV | Marathi | Legacy Shree fonts |
| `dvb-tt` | DVBWTTSurekh, DVBTTSurekh | Marathi | Government documents |
| `kruti-dev` | KrutiDev010, KrutiDev040 | Hindi | Common Hindi encoding |

Mapping files: `src/legacylipi/mappings/shree_dev.py`, `dvb_tt.py`, `loader.py`

## Translation Backends (translator.py)

| Backend | Class | Notes |
|---------|-------|-------|
| `trans` | `TranslateShellBackend` | **Recommended** - CLI tool, fast, requires `translate-shell` |
| `google` | `GoogleTranslateBackend` | Free web API, heavily rate limited |
| `mymemory` | `MyMemoryTranslationBackend` | Free, 500 char limit per request |
| `ollama` | `OllamaTranslationBackend` | Local LLM, requires Ollama server |
| `openai` | `OpenAITranslationBackend` | Requires API key |
| `mock` | `MockTranslationBackend` | For testing |

**Note:** Use `trans` (Translate-Shell) for best performance. Install with: `brew install translate-shell`

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

## Pre-Commit Checks

**IMPORTANT:** Always run the pre-commit checks before committing changes:

```bash
./scripts/check.sh
```

This runs:
1. **Linting** - `ruff check src/`
2. **Type checking** - `mypy src/legacylipi`
3. **Tests** - `pytest tests/ -v`

Only commit if all checks pass. CI will run the same checks on PRs.

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

**IMPORTANT:** Prefer CLI testing over Playwright for faster iteration. Use Playwright only for end-to-end UI verification.

### Quick CLI Testing (Preferred)

```bash
# Test full pipeline without UI
uv run python -c "
from legacylipi.core.pdf_parser import PDFParser
from legacylipi.core.encoding_detector import EncodingDetector
from legacylipi.core.unicode_converter import UnicodeConverter

parser = PDFParser('Javadekar.pdf')
doc = parser.parse()
detector = EncodingDetector()
result, _ = detector.detect_from_document(doc)
print(f'Encoding: {result.detected_encoding}, Confidence: {result.confidence}')

converter = UnicodeConverter()
for block in doc.pages[0].text_blocks[:3]:
    conv = converter.convert_text(block.raw_text, result.detected_encoding)
    print(f'Raw: {block.raw_text[:30]} -> Unicode: {conv.converted_text[:30]}')
"
```

### Playwright UI Testing (When Needed)

1. **Start the server**:
   ```bash
   uv run python -m legacylipi.ui.app > /tmp/legacylipi.log 2>&1 &
   sleep 5
   ```

2. **Test workflow**:
   - Navigate: `mcp__playwright__browser_navigate: http://localhost:8080`
   - Upload: Click "Choose File" → `mcp__playwright__browser_file_upload: ["/path/to/test.pdf"]`
   - Select backend: **Use "Translate-Shell (CLI)"** - it's fastest
   - Translate: Click "Translate" button
   - Wait: `mcp__playwright__browser_wait_for: Download` (may take 2-5 mins for large PDFs)

### Backend Selection for Testing

| Backend | Speed | Best For |
|---------|-------|----------|
| Translate-Shell | Fast | Production testing, recommended |
| Google Translate | Slow (rate limited) | Avoid for testing |
| MyMemory | Medium | Small files only (500 char limit) |
| Mock | Instant | Unit tests, pipeline verification |

### Test PDFs

| File | Size | Pages | Encoding | Notes |
|------|------|-------|----------|-------|
| `Javadekar.pdf` | 310KB | 6 | SHREE-DEV | Primary test file |
| `Marathi-Bhascyacha-vaapar.pdf` | 135KB | 11 | SHREE-DEV | Alternative test |

### Known Issues

- **MuPDF CID errors**: "unknown cid font type" warnings are normal for SHREE-DEV fonts - extraction still works
- **Google Translate rate limiting**: Use Translate-Shell instead
- **WebSocket timeout**: Fixed by batched UI updates (every 10 blocks)
