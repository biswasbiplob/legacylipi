# LegacyLipi

**Legacy Font PDF Translator** - Translate PDF documents with legacy Indian font encodings to English.

## Installation

### From PyPI (Recommended)

```bash
pip install legacylipi
```

Or with uv:

```bash
uv tool install legacylipi
```

### From Source

```bash
git clone https://github.com/biswasbiplob/legacylipi.git
cd legacylipi
uv sync
```

### Frontend (for development)

```bash
cd frontend
npm install
```

### Usage

```bash
# CLI translation
legacylipi translate input.pdf -o output.txt

# Launch React web UI (production build served by FastAPI)
legacylipi api

# Launch legacy NiceGUI web UI (deprecated)
legacylipi ui
```

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
3. **Alternatively**, uses **OCR** to extract text from scanned PDFs
4. **Translates** the Unicode text to the target language
5. **Outputs** translated text in various formats (text, markdown, PDF)

## Installation

```bash
# Clone and install
git clone https://github.com/biswasbiplob/legacylipi.git
cd legacylipi
uv sync

# With all optional backends
uv sync --all-extras
```

### OCR Support (Optional)

LegacyLipi supports multiple OCR backends:

| Backend | Description | GPU Support |
|---------|-------------|-------------|
| Tesseract | Local, free, most language packs | CPU only |
| Google Vision | Cloud, paid, best accuracy | N/A |
| EasyOCR | Local, free, good for Indian languages | CUDA, MPS (Apple Silicon) |

**Tesseract (default):**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-mar tesseract-ocr-hin

# macOS
brew install tesseract tesseract-lang
```

**EasyOCR with GPU (optional):**
```bash
# Install with EasyOCR support
uv sync --extra easyocr

# For GPU acceleration, install PyTorch with CUDA or MPS support
```

**Google Vision (optional):**
```bash
uv sync --extra vision
# Requires GCP credentials (GOOGLE_APPLICATION_CREDENTIALS)
```

See [docs/cli-reference.md](docs/cli-reference.md) for detailed OCR options and language codes.

## Quick Start

```bash
# Basic translation
uv run legacylipi translate input.pdf -o output.txt

# Output as PDF (preserves layout)
uv run legacylipi translate input.pdf -o output.pdf --format pdf

# OCR for scanned documents
uv run legacylipi translate input.pdf --use-ocr -o output.txt

# Use local LLM (requires Ollama)
uv run legacylipi translate input.pdf --translator ollama --model llama3.2

# Detect encoding only
uv run legacylipi detect input.pdf
```

See [docs/cli-reference.md](docs/cli-reference.md) for complete CLI documentation.

## Web UI

LegacyLipi includes a modern React-based web interface backed by a FastAPI REST API.

### Production (single command)

```bash
# Serves the built React frontend + API on one port
uv run legacylipi api
# or
uv run legacylipi-web
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

### Legacy NiceGUI UI (deprecated)

The original NiceGUI-based UI is still available but deprecated:

```bash
uv run legacylipi ui
# Open http://localhost:8080
```

**Workflow Modes:**
- **Scanned Copy** - Create image-based PDF copy (adjust DPI, color, quality)
- **Convert to Unicode** - OCR + Unicode conversion without translation
- **Full Translation** - Complete pipeline with OCR, conversion, and translation

**Features:**
- Drag-and-drop PDF upload
- Workflow-based UI with mode selection
- Multiple translation backends (Translate-Shell, Google, Ollama, OpenAI, etc.)
- OCR support with engine and language selection
- Structure-preserving or flowing text modes
- Real-time SSE progress streaming
- Direct download of translated files
- Responsive dark-theme design

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

## CLI Commands

| Command | Description |
|---------|-------------|
| `api` | Launch the React web UI + FastAPI REST API |
| `translate` | Full pipeline: parse → detect → convert → translate → output |
| `convert` | Convert legacy encoding to Unicode (no translation) |
| `extract` | Extract text from PDF (OCR or font-based) |
| `detect` | Analyze PDF and report detected encoding |
| `scan-copy` | Create an image-based scanned copy of a PDF |
| `encodings` | List supported font encodings |
| `usage` | Show API usage statistics |
| `ui` | Launch legacy NiceGUI web interface (deprecated) |

See [docs/cli-reference.md](docs/cli-reference.md) for full command reference.

## Development

See [docs/development.md](docs/development.md) for setup instructions, running tests, project structure, and adding new encodings.

### Architecture

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
│  │  PDF Parser / OCR Parser                                         │   │
│  │       │                                                          │   │
│  │  Encoding Detector → Unicode Converter                           │   │
│  │       │                                                          │   │
│  │  Translation Engine (trans, Google, Ollama, OpenAI, GCP, ...)    │   │
│  │       │                                                          │   │
│  │  Output Generator (.txt, .md, .pdf)                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pipeline Flow:**
1. **Parse PDF** → Extract text with PDF parser or OCR
2. **Detect Encoding** → Identify legacy encoding scheme
3. **Convert to Unicode** → Transform legacy text to Unicode
4. **Translate** → Use translation backend
5. **Generate Output** → Create PDF/text/markdown

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Commit and push
6. Open a Pull Request
