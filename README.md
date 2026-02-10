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
3. **Alternatively**, uses **OCR** (Tesseract or EasyOCR) to extract text from scanned PDFs
4. **Translates** the Unicode text to the target language
5. **Outputs** translated text in various formats (text, markdown, PDF) with optional bilingual side-by-side output

## Installation

### From PyPI (Recommended)

```bash
pip install legacylipi
```

Or with uv (one command, no install):

```bash
uvx legacylipi api
```

Or install as a tool:

```bash
uv tool install legacylipi
```

### From Source

```bash
git clone https://github.com/biswasbiplob/legacylipi.git
cd legacylipi
uv sync
```

### Docker

```bash
# Build the image
docker build -t legacylipi .

# Run with Docker
docker run -p 8000:8000 legacylipi

# Or use Docker Compose
docker compose up
```

The web UI will be available at http://localhost:8000.

To process local files, mount volumes:
```bash
docker run -p 8000:8000 -v ./input:/app/input -v ./output:/app/output legacylipi
```

### System Dependencies

**Tesseract** (for OCR - recommended):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-mar tesseract-ocr-hin

# macOS
brew install tesseract tesseract-lang
```

**Translate-Shell** (recommended translation backend):
```bash
# Ubuntu/Debian
sudo apt-get install translate-shell

# macOS
brew install translate-shell
```

## Quick Start

```bash
# Basic translation
legacylipi translate input.pdf -o output.txt

# Output as PDF (preserves layout)
legacylipi translate input.pdf -o output.pdf --format pdf

# Bilingual side-by-side output
legacylipi translate input.pdf -o output.pdf --bilingual

# OCR for scanned documents
legacylipi translate input.pdf --use-ocr -o output.txt

# Use local LLM (requires Ollama)
legacylipi translate input.pdf --translator ollama --model llama3.2

# Detect encoding only
legacylipi detect input.pdf
```

See [docs/cli-reference.md](docs/cli-reference.md) for complete CLI documentation.

## Web UI

LegacyLipi includes a modern React-based web interface backed by a FastAPI REST API.

### Production (single command)

```bash
# Serves the built React frontend + API on one port
legacylipi api
# or
uvx legacylipi api
```

Open **http://localhost:8000** in your browser.

### Development (hot-reload)

```bash
# Start both FastAPI backend and Vite dev server
./scripts/dev.sh
```

This runs:
- **Backend** at http://localhost:8000 (FastAPI with auto-reload)
- **Frontend** at http://localhost:5173 (Vite dev server with HMR, proxies `/api` to backend)

**Workflow Modes:**
- **Scanned Copy** - Create image-based PDF copy (adjust DPI, color, quality)
- **Convert to Unicode** - OCR + Unicode conversion without translation
- **Full Translation** - Complete pipeline with OCR, conversion, and translation

**Features:**
- Drag-and-drop PDF upload
- Workflow-based UI with mode selection
- Multiple translation backends (Translate-Shell, Google, Ollama, OpenAI, etc.)
- OCR support with EasyOCR and Tesseract engine selection
- Structure-preserving or flowing text modes
- Bilingual side-by-side output
- Source language auto-detection from encoding
- Real-time SSE progress streaming
- Direct download of translated files
- Responsive dark-theme design

## Supported Encodings

| Encoding | Font Family | Language | Status |
|----------|-------------|----------|--------|
| shree-dev | SHREE-DEV-0708, 0714, 0715, 0721 | Marathi | Built-in |
| shree-lipi | Shree-Lipi, SDL-DEV | Marathi | Built-in |
| dvb-tt | DVBWTTSurekh, DVBTTSurekh | Marathi | Built-in |
| kruti-dev | KrutiDev010, KrutiDev040 | Hindi | Built-in |
| chanakya | Chanakya | Hindi/Sanskrit | Built-in |
| aps-dv | APS-DV-TT | Hindi | Built-in |
| walkman-chanakya | Walkman Chanakya | Hindi | Built-in |
| shusha | Shusha | Marathi/Hindi | Built-in |

## Translation Backends

| Backend | Description | Setup |
|---------|-------------|-------|
| `trans` | translate-shell CLI (recommended) | `brew install translate-shell` |
| `google` | Google Translate (free API) | Works out of the box |
| `mymemory` | MyMemory API (free) | Works out of the box |
| `ollama` | Local LLM via Ollama | [Ollama](https://ollama.ai) required |
| `openai` | OpenAI GPT models | Set `OPENAI_API_KEY` |
| `gcp_cloud` | Google Cloud Translation | GCP project + credentials |

See [docs/translation-backends.md](docs/translation-backends.md) for detailed setup guides.

## OCR Backends

Both OCR engines are included as core dependencies:

| Backend | Description | GPU Support |
|---------|-------------|-------------|
| EasyOCR | Local, free, good for Indian languages (default) | CUDA, MPS (Apple Silicon) |
| Tesseract | Local, free, most language packs | CPU only |
| Google Vision | Cloud, paid, best accuracy | N/A |

Google Vision requires an additional install: `pip install legacylipi[vision]`

See [docs/cli-reference.md](docs/cli-reference.md) for detailed OCR options and language codes.

## CLI Commands

| Command | Description |
|---------|-------------|
| `api` | Launch the React web UI + FastAPI REST API |
| `translate` | Full pipeline: parse, detect, convert, translate, output |
| `convert` | Convert legacy encoding to Unicode (no translation) |
| `extract` | Extract text from PDF (OCR or font-based) |
| `detect` | Analyze PDF and report detected encoding |
| `scan-copy` | Create an image-based scanned copy of a PDF |
| `encodings` | List supported font encodings |
| `usage` | Show API usage statistics |

See [docs/cli-reference.md](docs/cli-reference.md) for full command reference.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LegacyLipi                                 │
├─────────────────────┬───────────────────────────────────────────────────┤
│   React Frontend    │                  FastAPI Backend                   │
│  (Vite + TS + TW)   │                                                   │
│                     │   ┌──────────────────────────────────────────┐    │
│  FileUploader       │   │              REST API                    │    │
│  WorkflowSelector   │   │  /api/v1/config/*     GET config         │    │
│  Settings panels    │◄─▶│  /api/v1/sessions/*   Upload/delete      │    │
│  StatusPanel (SSE)  │   │  /api/v1/sessions/*/  Start pipeline     │    │
│  DownloadButton     │   │  /api/v1/sessions/*/progress  SSE stream │    │
│                     │   │  /api/v1/sessions/*/download  Get result │    │
│                     │   └────────────────────┬─────────────────────┘    │
├─────────────────────┘                        │                          │
│                                              ▼                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Core Pipeline                               │   │
│  │                                                                  │   │
│  │  PDF Parser / OCR Parser (Tesseract + EasyOCR)                   │   │
│  │       │                                                          │   │
│  │  Encoding Detector → Unicode Converter                           │   │
│  │       │                                                          │   │
│  │  Translation Engine (trans, Google, Ollama, OpenAI, GCP, ...)    │   │
│  │       │                                                          │   │
│  │  Output Generator (.txt, .md, .pdf, bilingual)                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Development

See [docs/development.md](docs/development.md) for setup instructions, running tests, project structure, and adding new encodings.

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run checks (`./scripts/check.sh`)
4. Commit and push
5. Open a Pull Request
