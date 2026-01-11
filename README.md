# LegacyLipi

**Legacy Font PDF Translator** - Translate PDF documents with legacy Indian font encodings to English.

## Problem

Millions of government documents, legal papers, and archival materials in Indian regional languages (Marathi, Hindi, Tamil, etc.) were created using legacy font encoding systems (Shree-Lipi, Kruti Dev, APS, Chanakya, etc.). These fonts map Devanagari/regional script glyphs to ASCII/Latin code points, making them unreadable by standard translation tools.

**Example:**
- What the PDF displays: महाराष्ट्र राजभाषा अधिनियम
- What text extraction produces: `´ÖÆüÖ¸üÖÂ™Òü ¸üÖ•Ö³ÖÖÂÖÖ †×¬Ö×®ÖμÖ´Ö`
- What Google Translate sees: Gibberish

## Solution

LegacyLipi:
1. **Detects** the font encoding scheme used in a PDF (legacy or Unicode)
2. **Converts** legacy-encoded text to proper Unicode
3. **Alternatively**, uses **OCR** to extract text from scanned PDFs or when font-based extraction fails
4. **Translates** the Unicode text to the target language
5. **Outputs** translated text in various formats (text, markdown, PDF)

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/biswasbiplob/context-engineered-tools.git
cd context-engineered-tools

# Install dependencies
uv sync

# Run with uv
uv run legacylipi --help
```

### With optional backends

```bash
# Install with Google Translate support
uv sync --extra google

# Install with Ollama (local LLM) support
uv sync --extra ollama

# Install all optional dependencies
uv sync --all-extras
```

### OCR Support (Optional)

For OCR-based text extraction from scanned PDFs, install Tesseract OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-mar tesseract-ocr-hin
```

**macOS (Homebrew):**
```bash
brew install tesseract
brew install tesseract-lang  # Includes all language packs
# Or install specific languages:
# brew install tesseract && brew install tesseract-lang
```

**Windows:**
1. Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. During installation, select additional languages (Marathi, Hindi, etc.)
3. Add Tesseract to your PATH

**Verify installation:**
```bash
tesseract --version
tesseract --list-langs  # Should include 'mar' for Marathi
```

## Quick Start

```bash
# Basic translation (auto-detect encoding, use Google Translate)
uv run legacylipi translate tests/data/input.pdf -o output.txt

# Output as Markdown
uv run legacylipi translate tests/data/input.pdf -o output.md --format markdown

# Output as PDF (preserves original layout)
uv run legacylipi translate tests/data/input.pdf -o output.pdf --format pdf

# Use local LLM for translation (requires Ollama running)
uv run legacylipi translate tests/data/input.pdf --translator ollama --model llama3.2

# Use OpenAI for translation (requires OPENAI_API_KEY)
uv run legacylipi translate tests/data/input.pdf --translator openai

# Just convert to Unicode (no translation)
uv run legacylipi convert tests/data/input.pdf -o unicode_output.txt

# Extract text only (no translation) - supports OCR and font-based
uv run legacylipi extract tests/data/input.pdf -o extracted.txt

# Extract with OCR
uv run legacylipi extract tests/data/input.pdf --use-ocr -o marathi.txt

# Detect encoding only
uv run legacylipi detect tests/data/input.pdf

# Detect with verbose page-by-page analysis
uv run legacylipi detect tests/data/input.pdf --verbose

# Force specific encoding
uv run legacylipi translate tests/data/input.pdf --encoding shree-lipi

# List supported encodings
uv run legacylipi encodings
```

### OCR Mode (for scanned PDFs)

When font-based extraction fails or for scanned documents, use OCR:

```bash
# OCR with Marathi language (default)
uv run legacylipi translate tests/data/input.pdf --use-ocr -o output.txt

# OCR with Hindi language
uv run legacylipi translate tests/data/input.pdf --use-ocr --ocr-lang hin -o output.txt

# OCR with higher DPI for better accuracy (slower)
uv run legacylipi translate tests/data/input.pdf --use-ocr --ocr-dpi 600 -o output.txt

# OCR without translation (extract original text only)
uv run legacylipi translate tests/data/input.pdf --use-ocr --no-translate -o marathi.txt

# OCR with translate-shell backend
uv run legacylipi translate tests/data/input.pdf --use-ocr --translator trans -o output.txt
```

## CLI Commands

### `translate`
Full translation pipeline: parse → detect → convert → translate → output

```bash
uv run legacylipi translate INPUT_FILE [OPTIONS]

Options:
  -o, --output PATH               Output file path
  --format [text|markdown|md|pdf] Output format (default: text)
  --encoding TEXT                 Force specific encoding
  --target-lang TEXT              Target language code (default: en)
  --translator [mock|google|trans|mymemory|ollama|openai]
                                  Translation backend
  --model TEXT                    Model for Ollama or OpenAI backend
  --trans-path TEXT               Path to trans executable (for --translator trans)
  --no-translate                  Skip translation, only convert to Unicode
  --use-ocr                       Use OCR instead of font-based extraction
  --ocr-lang TEXT                 OCR language code (default: mar)
  --ocr-dpi INTEGER               OCR rendering DPI (default: 300)
  -q, --quiet                     Suppress progress output
```

### `convert`
Convert legacy encoding to Unicode without translation

```bash
uv run legacylipi convert INPUT_FILE [OPTIONS]

Options:
  -o, --output PATH      Output file path
  --encoding TEXT        Force specific encoding
```

### `extract`
Extract text from PDF (OCR or font-based) without translation

```bash
uv run legacylipi extract INPUT_FILE [OPTIONS]

Options:
  -o, --output PATH               Output file path
  --format [text|markdown|md|pdf] Output format (default: text)
  --encoding TEXT                 Force specific encoding
  --use-ocr                       Use OCR instead of font-based extraction
  --ocr-lang TEXT                 OCR language code (default: mar)
  --ocr-dpi INTEGER               OCR rendering DPI (default: 300)
  -q, --quiet                     Suppress progress output
```

**Examples:**
```bash
# Extract using font-based method (with legacy encoding conversion)
uv run legacylipi extract tests/data/input.pdf -o marathi.txt

# Extract using OCR (for scanned documents)
uv run legacylipi extract tests/data/input.pdf --use-ocr -o marathi.txt

# Extract with OCR to PDF format (preserves structure)
uv run legacylipi extract tests/data/input.pdf --use-ocr -o output.pdf --format pdf

# Extract with Hindi OCR at higher quality
uv run legacylipi extract tests/data/input.pdf --use-ocr --ocr-lang hin --ocr-dpi 600 -o hindi.txt
```

### `detect`
Analyze PDF and report detected encoding

```bash
uv run legacylipi detect INPUT_FILE [OPTIONS]

Options:
  -v, --verbose          Show page-by-page analysis
```

### `encodings`
List supported font encodings

```bash
uv run legacylipi encodings [OPTIONS]

Options:
  -s, --search TEXT      Search for encoding by name
```

## Supported Encodings

| Encoding | Font Family | Language | Status |
|----------|-------------|----------|--------|
| shree-lipi | Shree-Lipi, Shree-Dev-0714 | Marathi | ✅ Built-in |
| kruti-dev | Kruti Dev | Hindi | ✅ Built-in |
| aps-dv | APS-DV | Hindi | 🔄 Detection only |
| chanakya | Chanakya | Hindi | 🔄 Detection only |
| dvb-tt | DVB-TT, DV-TTYogesh | Hindi | 🔄 Detection only |
| walkman-chanakya | Walkman Chanakya | Hindi | 🔄 Detection only |
| shusha | Shusha | Hindi | 🔄 Detection only |

## Translation Backends

| Backend | Description | Setup | Rate Limiting |
|---------|-------------|-------|---------------|
| `trans` | translate-shell CLI (recommended) | Install: `brew install translate-shell` or download `wget git.io/trans` | Built-in: 2s delay, auto-retry |
| `google` | Google Translate (free API) | Works out of the box | Built-in: delays + retries |
| `mymemory` | MyMemory API (free) | Works out of the box | 500 char limit per request |
| `ollama` | Local LLM via Ollama | Requires [Ollama](https://ollama.ai) running locally | No limits (local) |
| `openai` | OpenAI GPT models | Set `OPENAI_API_KEY` environment variable | API rate limits apply |
| `mock` | Mock translator for testing | Always available | N/A |

### Using translate-shell (Recommended)

translate-shell (`trans`) is a command-line translator that works reliably. LegacyLipi's `trans` backend includes:
- **Rate limiting**: 2 second delay with random jitter between chunks
- **Auto-retry**: Up to 3 retries with exponential backoff for rate-limit errors
- **Adaptive timeout**: Starts at 60s, increases on retry (up to 180s)
- **Smaller chunks**: Text split into 2000-char chunks to avoid API limits

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install translate-shell

# macOS
brew install translate-shell

# Manual install (any platform)
wget git.io/trans && chmod +x trans
```

**Use:**
```bash
# Default (uses Google Translate engine via trans CLI)
uv run legacylipi translate tests/data/input.pdf --translator trans

# With custom path to trans executable
uv run legacylipi translate tests/data/input.pdf --translator trans --trans-path ./trans

# With OCR for scanned documents
uv run legacylipi translate tests/data/input.pdf --use-ocr --translator trans -o output.pdf --format pdf
```

### Using Ollama

```bash
# Start Ollama (in another terminal)
ollama serve

# Pull a model
ollama pull llama3.2

# Use with LegacyLipi
uv run legacylipi translate tests/data/input.pdf --translator ollama --model llama3.2
```

### Using OpenAI

Use OpenAI's GPT models for high-quality translation:

```bash
# Set your API key
export OPENAI_API_KEY="your-api-key-here"

# Use with default model (gpt-4o-mini)
uv run legacylipi translate tests/data/input.pdf --translator openai

# Use with a specific model
uv run legacylipi translate tests/data/input.pdf --translator openai --model gpt-4o
```

**Available models:**
- `gpt-4o-mini` (default) - Fast and cost-effective
- `gpt-4o` - Most capable, best for complex translations
- `gpt-3.5-turbo` - Faster, lower cost

## OCR Support

LegacyLipi supports OCR-based text extraction using Tesseract OCR. This is useful when:
- The PDF is a scanned document (image-based)
- Font-based text extraction produces garbled output
- The legacy font mapping is not available

### OCR Language Codes

| Language | Code | Tesseract Package |
|----------|------|-------------------|
| Marathi | `mar` | `tesseract-ocr-mar` |
| Hindi | `hin` | `tesseract-ocr-hin` |
| English | `eng` | `tesseract-ocr-eng` (usually pre-installed) |
| Tamil | `tam` | `tesseract-ocr-tam` |
| Telugu | `tel` | `tesseract-ocr-tel` |
| Kannada | `kan` | `tesseract-ocr-kan` |
| Malayalam | `mal` | `tesseract-ocr-mal` |
| Gujarati | `guj` | `tesseract-ocr-guj` |
| Bengali | `ben` | `tesseract-ocr-ben` |
| Punjabi | `pan` | `tesseract-ocr-pan` |

### OCR Tips

1. **Higher DPI = Better accuracy** (but slower): Use `--ocr-dpi 600` for poor quality scans
2. **Pre-process images**: Clean, high-contrast scans work best
3. **Language matters**: Always specify the correct `--ocr-lang` for best results
4. **Combine with translation**: OCR extracts original text, then translate as usual

---

## Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/biswasbiplob/context-engineered-tools.git
cd context-engineered-tools

# Install all dependencies (including dev)
uv sync --all-extras
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_models.py -v

# Run with coverage
uv run pytest --cov=src/legacylipi --cov-report=html

# Run only fast tests (exclude slow/integration)
uv run pytest -m "not slow"
```

### Code Quality

```bash
# Run linter
uv run ruff check src/ tests/

# Run linter with auto-fix
uv run ruff check --fix src/ tests/

# Run type checker
uv run mypy src/legacylipi/
```

### Project Structure

```
src/legacylipi/
├── __init__.py              # Package exports
├── cli.py                   # CLI interface (Click)
├── core/
│   ├── models.py            # Data models (PDFDocument, TextBlock, etc.)
│   ├── pdf_parser.py        # PDF parsing with PyMuPDF
│   ├── ocr_parser.py        # OCR-based PDF text extraction (Tesseract)
│   ├── encoding_detector.py # Legacy font detection
│   ├── unicode_converter.py # Legacy-to-Unicode conversion
│   ├── translator.py        # Translation backends (Google, trans, MyMemory, Ollama, OpenAI)
│   └── output_generator.py  # Text/Markdown/PDF output generation
├── mappings/
│   └── loader.py            # Font mapping tables
└── utils/                   # Utility functions

tests/
├── conftest.py              # Pytest fixtures
├── test_models.py           # Data model tests
├── test_pdf_parser.py       # PDF parser tests
├── test_ocr_parser.py       # OCR parser tests
├── test_encoding_detector.py # Encoding detection tests
├── test_unicode_converter.py # Unicode conversion tests
├── test_mappings.py         # Mapping loader tests
├── test_translator.py       # Translation engine tests
├── test_output_generator.py # Output generator tests
├── test_cli.py              # CLI tests
└── test_integration.py      # End-to-end integration tests
```

### Adding a New Encoding

1. Create a mapping file in `data/mappings/` (YAML or JSON):

```yaml
# data/mappings/my-font.yaml
metadata:
  font_family: "My Font"
  language: "Hindi"
  script: "Devanagari"
  version: "1.0"

mappings:
  "a": "अ"
  "b": "ब"
  # ... more character mappings

ligatures:
  "ksh": "क्ष"
  # ... ligature mappings

half_forms:
  "k~": "क्"
  # ... half form mappings
```

2. Add font name patterns to `encoding_detector.py`:

```python
LegacyFontPattern(
    encoding_name="my-font",
    patterns=[r"my[-_]font", r"myfont"],
    signatures=["unique", "text", "signatures"],
    priority=5,
)
```

3. Add tests for the new encoding.

### Making a Release

```bash
# Update version in pyproject.toml and __init__.py
# Then:
uv build
uv publish  # (when ready for PyPI)
```

### Common Development Tasks

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update dependencies
uv lock --upgrade

# Sync after pulling changes
uv sync
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LegacyLipi                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Text Extraction                              │   │
│  │  ┌──────────────┐              ┌──────────────┐                   │   │
│  │  │   PDF        │    OR        │   OCR        │                   │   │
│  │  │   Parser     │              │   Parser     │                   │   │
│  │  │ (font-based) │              │ (Tesseract)  │                   │   │
│  │  └──────────────┘              └──────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                                │                               │
│         ▼                                ▼                               │
│  ┌──────────────┐    ┌──────────────┐                                   │
│  │   Encoding   │───▶│   Unicode    │◀──── (OCR output is               │
│  │   Detector   │    │   Converter  │       already Unicode)            │
│  └──────────────┘    └──────────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│         ┌───────────────────────────────────────────────────────┐       │
│         │                 Translation Engine                      │       │
│         │  ┌────────┬────────┬──────────┬────────┬────────┬────┐ │       │
│         │  │ trans  │ Google │ MyMemory │ Ollama │ OpenAI │Mock│ │       │
│         │  │ (CLI)  │ Trans. │  (API)   │(Local) │ (API)  │    │ │       │
│         │  └────────┴────────┴──────────┴────────┴────────┴────┘ │       │
│         └───────────────────────────────────────────────────────┘       │
│                             │                                            │
│                             ▼                                            │
│         ┌───────────────────────────────────────────────┐               │
│         │            Output Generator                    │               │
│         │  ┌──────┬────────┬───────┐                    │               │
│         │  │ .txt │  .md   │ .pdf  │                    │               │
│         │  └──────┴────────┴───────┘                    │               │
│         └───────────────────────────────────────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request
