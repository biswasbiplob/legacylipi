# LegacyLipi v1.0.0

The first stable release of LegacyLipi — a PDF translator for legacy Indian font encodings (Marathi, Hindi, Sanskrit).

## Highlights

- **New React web interface** replacing the legacy NiceGUI UI — modern, responsive, and fast
- **8 encoding mappings** covering the most common legacy Devanagari fonts
- **Batteries included** — a single `pip install legacylipi` gets you everything: web UI, CLI, OCR, and API

## What's New (since v0.8.0)

### Web Interface
- Full React 19 + TypeScript frontend served by FastAPI
- Source language auto-detection dropdown
- Bilingual output toggle
- Real-time translation progress via SSE

### Encoding Support
- **4 new encodings**: Chanakya, APS-DV, Walkman-Chanakya, Shusha
- Improved detection with character frequency analysis and confidence weighting
- Generic Devanagari post-processing pipeline (matra reordering, nukta handling, visarga positioning)

### Translation Pipeline
- Per-page translation — eliminates page marker corruption
- Source language auto-detection from encoding metadata
- Bilingual output mode (original + translated side by side)

### Infrastructure
- Bundled Noto Sans Devanagari font — PDF output works on any system
- Docker support with multi-stage build (`docker-compose up`)
- 523 tests across 13 test files

### Breaking Changes
- **NiceGUI UI removed** — `legacylipi-ui` entry point and `legacylipi ui` command no longer exist. Use `legacylipi api` instead.
- **All dependencies are now core** — `[api]`, `[ocr]`, and `[ui]` extras have been removed. Everything installs by default.

## Supported Encodings

| Encoding | Language | Common Fonts |
|----------|----------|-------------|
| Shree-Dev | Marathi | SHREE-DEV-0708, 0714, 0715, 0721 |
| Shree-Lipi | Marathi | Shree-Lipi, SDL-DEV |
| DVB-TT | Marathi | DVBWTTSurekh, DVBTTSurekh |
| Kruti-Dev | Hindi | KrutiDev010, KrutiDev040 |
| Chanakya | Hindi/Sanskrit | Chanakya |
| APS-DV | Hindi | APS-DV-Yogesh, APS-DV-Prakash |
| Walkman-Chanakya | Hindi | Walkman-Chanakya |
| Shusha | Marathi/Hindi | Shusha, SHU-0751 |

## Quick Start

```bash
# Install
pip install legacylipi
# or
uv tool install legacylipi

# Launch web UI
legacylipi api

# CLI usage
legacylipi translate input.pdf -o output.pdf
legacylipi translate input.pdf -o output.pdf --bilingual
legacylipi detect input.pdf
```

## Docker

```bash
docker compose up
# Open http://localhost:8000
```
