# CLI Reference

Complete command-line interface documentation for LegacyLipi.

## Commands Overview

| Command | Description |
|---------|-------------|
| `translate` | Full translation pipeline: parse → detect → convert → translate → output |
| `convert` | Convert legacy encoding to Unicode without translation |
| `extract` | Extract text from PDF (OCR or font-based) without translation |
| `detect` | Analyze PDF and report detected encoding |
| `encodings` | List supported font encodings |
| `usage` | Show API usage statistics for translation services |

---

## translate

Full translation pipeline: parse → detect → convert → translate → output

```bash
uv run legacylipi translate INPUT_FILE [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output file path | - |
| `--format [text\|markdown\|md\|pdf]` | Output format | text |
| `--encoding TEXT` | Force specific encoding | auto-detect |
| `--target-lang TEXT` | Target language code | en |
| `--translator [mock\|google\|trans\|mymemory\|ollama\|openai\|gcp_cloud]` | Translation backend | google |
| `--model TEXT` | Model for Ollama or OpenAI backend | - |
| `--trans-path TEXT` | Path to trans executable | trans |
| `--gcp-project TEXT` | GCP project ID (required for gcp_cloud) | - |
| `--force-translate` | Continue even if GCP free tier limit exceeded | false |
| `--no-translate` | Skip translation, only convert to Unicode | false |
| `--use-ocr` | Use OCR instead of font-based extraction | false |
| `--ocr-lang TEXT` | OCR language code | mar |
| `--ocr-dpi INTEGER` | OCR rendering DPI | 300 |
| `--structure-preserving` | Preserve original text positions in PDF output | false |
| `-q, --quiet` | Suppress progress output | false |

### Examples

```bash
# Basic translation (auto-detect encoding, use Google Translate)
uv run legacylipi translate input.pdf -o output.txt

# Output as PDF (preserves original layout)
uv run legacylipi translate input.pdf -o output.pdf --format pdf

# Use local LLM for translation
uv run legacylipi translate input.pdf --translator ollama --model llama3.2

# Use OpenAI for translation
uv run legacylipi translate input.pdf --translator openai

# OCR with Marathi language
uv run legacylipi translate input.pdf --use-ocr -o output.txt

# OCR with Hindi language and higher DPI
uv run legacylipi translate input.pdf --use-ocr --ocr-lang hin --ocr-dpi 600 -o output.txt

# Force specific encoding
uv run legacylipi translate input.pdf --encoding shree-lipi
```

---

## convert

Convert legacy encoding to Unicode without translation.

```bash
uv run legacylipi convert INPUT_FILE [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output file path | - |
| `--encoding TEXT` | Force specific encoding | auto-detect |

### Examples

```bash
# Convert to Unicode (no translation)
uv run legacylipi convert input.pdf -o unicode_output.txt

# Force specific encoding
uv run legacylipi convert input.pdf --encoding kruti-dev -o output.txt
```

---

## extract

Extract text from PDF (OCR or font-based) without translation.

```bash
uv run legacylipi extract INPUT_FILE [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output file path | - |
| `--format [text\|markdown\|md\|pdf]` | Output format | text |
| `--encoding TEXT` | Force specific encoding | auto-detect |
| `--use-ocr` | Use OCR instead of font-based extraction | false |
| `--ocr-lang TEXT` | OCR language code | mar |
| `--ocr-dpi INTEGER` | OCR rendering DPI | 300 |
| `-q, --quiet` | Suppress progress output | false |

### Examples

```bash
# Extract using font-based method (with legacy encoding conversion)
uv run legacylipi extract input.pdf -o marathi.txt

# Extract using OCR (for scanned documents)
uv run legacylipi extract input.pdf --use-ocr -o marathi.txt

# Extract with OCR to PDF format (preserves structure)
uv run legacylipi extract input.pdf --use-ocr -o output.pdf --format pdf

# Extract with Hindi OCR at higher quality
uv run legacylipi extract input.pdf --use-ocr --ocr-lang hin --ocr-dpi 600 -o hindi.txt
```

---

## detect

Analyze PDF and report detected encoding.

```bash
uv run legacylipi detect INPUT_FILE [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-v, --verbose` | Show page-by-page analysis | false |

### Examples

```bash
# Detect encoding
uv run legacylipi detect input.pdf

# Detect with verbose page-by-page analysis
uv run legacylipi detect input.pdf --verbose
```

---

## encodings

List supported font encodings.

```bash
uv run legacylipi encodings [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --search TEXT` | Search for encoding by name | - |

### Examples

```bash
# List all encodings
uv run legacylipi encodings

# Search for specific encoding
uv run legacylipi encodings --search shree
```

---

## usage

Show API usage statistics for translation services.

```bash
uv run legacylipi usage [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--service TEXT` | Service to check usage for | gcp_translate |

### Examples

```bash
# Check current GCP Cloud Translation usage
uv run legacylipi usage

# Check GCP usage explicitly
uv run legacylipi usage --service gcp_translate
```

### Output

Shows the current month, characters used, free tier limit, remaining quota, and usage percentage.

---

## OCR Language Codes

| Language | Code | Tesseract Package |
|----------|------|-------------------|
| Marathi | `mar` | `tesseract-ocr-mar` |
| Hindi | `hin` | `tesseract-ocr-hin` |
| English | `eng` | `tesseract-ocr-eng` |
| Tamil | `tam` | `tesseract-ocr-tam` |
| Telugu | `tel` | `tesseract-ocr-tel` |
| Kannada | `kan` | `tesseract-ocr-kan` |
| Malayalam | `mal` | `tesseract-ocr-mal` |
| Gujarati | `guj` | `tesseract-ocr-guj` |
| Bengali | `ben` | `tesseract-ocr-ben` |
| Punjabi | `pan` | `tesseract-ocr-pan` |

## OCR Tips

1. **Higher DPI = Better accuracy** (but slower): Use `--ocr-dpi 600` for poor quality scans
2. **Pre-process images**: Clean, high-contrast scans work best
3. **Language matters**: Always specify the correct `--ocr-lang` for best results
4. **Combine with translation**: OCR extracts original text, then translate as usual
