# Product Requirements Document (PRD)

> **Note:** This is an internal planning document from the initial project design phase.
> Current implementation may differ. See [README](../../README.md) for current features.

# LegacyLipi: Legacy Font PDF Translator

**Version:** 1.0 (Planning)
**Date:** January 7, 2026
**Author:** Biplob Biswas
**Status:** Historical Planning Document

---

## Executive Summary

LegacyLipi is a local desktop tool that solves a critical problem in Indian regional language document processing: **translating PDF documents that use legacy/proprietary font encodings** to English (or other languages). Unlike standard translation tools that fail on legacy-encoded documents, LegacyLipi auto-detects font encoding schemes, converts them to Unicode, and then performs accurate translation while optionally preserving document layout.

---

## Problem Statement

### The Core Issue

Millions of government documents, legal papers, and archival materials in Indian regional languages (Marathi, Hindi, Tamil, etc.) were created using **legacy font encoding systems** from the 1990s-2010s. These fonts (Shree-Lipi, Kruti Dev, APS, Chanakya, etc.) map Devanagari/regional script glyphs to ASCII/Latin code points.

**Example from the uploaded document:**
- **What the PDF displays:** महाराष्ट्र राजभाषा अधिनियम (rendered via legacy font)
- **What text extraction produces:** `´ÖÆüÖ¸üÖÂ™Òü ¸üÖ•Ö³ÖÖÂÖÖ †×¬Ö×®ÖμÖ´Ö`
- **What Google Translate sees:** Gibberish Latin characters
- **Result:** Translation completely fails

### Why Existing Solutions Fail

| Tool | Failure Mode |
|------|--------------|
| Google Translate | Cannot interpret legacy encoding; produces garbage |
| Adobe Acrobat | Extracts visual glyphs as-is; no encoding detection |
| OCR Tools | May recognize glyphs but cannot map to Unicode |
| DeepL/ChatGPT | Same issue as Google Translate |

### Impact

- Government transparency suffers (citizens cannot read translated official documents)
- Legal documents remain inaccessible to non-native speakers
- Historical/archival documents are locked in obsolete formats
- Cross-border business documentation is hindered

---

## Solution Overview

LegacyLipi is a **local CLI/GUI tool** that:

1. **Detects** the font encoding scheme used in a PDF (legacy or Unicode)
2. **Converts** legacy-encoded text to proper Unicode
3. **Translates** the Unicode text to the target language
4. **Outputs** either a translated PDF (preserving layout) or a clean text/markdown file

### Key Differentiator

The **auto-detection and mapping of 50+ legacy Indian font encodings** is the core USP. No existing consumer tool does this reliably.

---

## User Stories

### Primary User Story
> As a user with a Marathi/Hindi PDF that uses legacy fonts, I want to translate it to English so that I can understand the document contents without learning the source language.

### Secondary User Stories

1. **As a lawyer**, I want to translate old court documents in legacy Marathi fonts to English for my international clients.

2. **As a government official**, I want to make legacy documents accessible to English-speaking stakeholders.

3. **As a researcher**, I want to process archival documents in legacy encodings for academic analysis.

4. **As a business professional**, I want to understand vendor contracts written in regional languages with legacy fonts.

---

## Functional Requirements

### FR-1: PDF Input Processing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Accept PDF files as input (single file) | P0 |
| FR-1.2 | Extract embedded font information from PDF | P0 |
| FR-1.3 | Extract text content with positional metadata | P0 |
| FR-1.4 | Handle multi-page documents | P0 |
| FR-1.5 | Support password-protected PDFs (with password input) | P2 |

### FR-2: Font Encoding Detection (Core USP)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Detect if text is already Unicode | P0 |
| FR-2.2 | Identify legacy font family from embedded font metadata | P0 |
| FR-2.3 | Implement heuristic detection when font metadata is missing | P0 |
| FR-2.4 | Support Shree-Lipi font family (multiple variants) | P0 |
| FR-2.5 | Support Kruti Dev font family | P0 |
| FR-2.6 | Support APS font family | P1 |
| FR-2.7 | Support Chanakya font family | P1 |
| FR-2.8 | Support DVB/DV-TTYogesh fonts | P1 |
| FR-2.9 | Support Walkman Chanakya | P1 |
| FR-2.10 | Support Shusha fonts | P2 |
| FR-2.11 | Support South Indian legacy fonts (Tamil, Telugu, Kannada) | P2 |
| FR-2.12 | Provide confidence score for encoding detection | P1 |
| FR-2.13 | Allow manual encoding override | P1 |

### FR-3: Legacy to Unicode Conversion

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Maintain accurate character mapping tables for each font family | P0 |
| FR-3.2 | Handle conjunct characters (ligatures) correctly | P0 |
| FR-3.3 | Preserve word boundaries and spacing | P0 |
| FR-3.4 | Handle mixed-encoding documents (e.g., English + legacy Marathi) | P0 |
| FR-3.5 | Support half-characters and matra combinations | P0 |
| FR-3.6 | Log conversion warnings for ambiguous mappings | P1 |

### FR-4: Translation Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Translate Unicode text to target language (default: English) | P0 |
| FR-4.2 | Support multiple translation backends (configurable) | P1 |
| FR-4.3 | Option to use local LLM for translation (Ollama integration) | P1 |
| FR-4.4 | Option to use cloud APIs (Google Translate, DeepL, OpenAI) | P1 |
| FR-4.5 | Chunk large documents for API limits | P0 |
| FR-4.6 | Preserve paragraph structure during translation | P0 |
| FR-4.7 | Support 10+ target languages | P2 |

### FR-5: Output Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Output translated text as plain text file | P0 |
| FR-5.2 | Output translated text as Markdown | P0 |
| FR-5.3 | Output side-by-side bilingual document | P1 |
| FR-5.4 | Output translated PDF preserving original layout | P2 |
| FR-5.5 | Output intermediate Unicode text (for verification) | P1 |
| FR-5.6 | Include metadata about source encoding detected | P1 |

### FR-6: User Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | Command-line interface (CLI) for all operations | P0 |
| FR-6.2 | Simple GUI for drag-and-drop operation | P1 |
| FR-6.3 | Progress indication for long documents | P0 |
| FR-6.4 | Error messages with actionable guidance | P0 |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Process a 10-page PDF in under 60 seconds (excluding API latency) | P0 |
| NFR-1.2 | Memory usage under 500MB for typical documents | P0 |
| NFR-1.3 | Support documents up to 500 pages | P1 |

### NFR-2: Accuracy

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Font encoding detection accuracy > 95% for supported fonts | P0 |
| NFR-2.2 | Unicode conversion accuracy > 99% for detected encodings | P0 |
| NFR-2.3 | Zero data loss for Unicode-encoded source documents | P0 |

### NFR-3: Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | Run on Windows 10/11 | P0 |
| NFR-3.2 | Run on macOS 12+ | P0 |
| NFR-3.3 | Run on Ubuntu 20.04+ / major Linux distros | P0 |
| NFR-3.4 | No internet required for encoding detection and conversion | P0 |

### NFR-4: Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | Single-command operation for basic use case | P0 |
| NFR-4.2 | Clear documentation with examples | P0 |
| NFR-4.3 | Meaningful error messages | P0 |

### NFR-5: Extensibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-5.1 | Plugin architecture for new font encodings | P1 |
| NFR-5.2 | Configurable translation backend | P1 |
| NFR-5.3 | Mapping table format documented for community contributions | P1 |

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LegacyLipi                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   PDF        │    │   Encoding   │    │   Unicode    │               │
│  │   Parser     │───▶│   Detector   │───▶│   Converter  │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Font       │    │   Mapping    │    │   Clean      │               │
│  │   Metadata   │    │   Tables     │    │   Unicode    │               │
│  │   Extractor  │    │   (50+)      │    │   Text       │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                                                 │                        │
│                                                 ▼                        │
│                           ┌─────────────────────────────────┐           │
│                           │     Translation Engine          │           │
│                           │  ┌─────────┬─────────┬───────┐  │           │
│                           │  │ Ollama  │ Google  │ OpenAI│  │           │
│                           │  │ (Local) │ Trans.  │  API  │  │           │
│                           │  └─────────┴─────────┴───────┘  │           │
│                           └─────────────────────────────────┘           │
│                                                 │                        │
│                                                 ▼                        │
│                           ┌─────────────────────────────────┐           │
│                           │      Output Generator           │           │
│                           │  ┌──────┬────────┬──────────┐   │           │
│                           │  │ .txt │  .md   │   .pdf   │   │           │
│                           │  └──────┴────────┴──────────┘   │           │
│                           └─────────────────────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. PDF Parser
- **Library:** PyMuPDF (fitz) or pdfplumber
- **Responsibility:** Extract text streams, font metadata, positional data
- **Output:** Raw text + font info per text block

#### 2. Font Metadata Extractor
- Extract embedded font names from PDF
- Parse font descriptor for encoding hints
- Handle cases where fonts are subset or renamed

#### 3. Encoding Detector
- **Primary method:** Match font name against known legacy font database
- **Fallback method:** Heuristic analysis of character patterns
- **Confidence scoring:** Return detection confidence (high/medium/low)

#### 4. Mapping Tables Database
- JSON/YAML files containing character mappings
- Structure:
  ```json
  {
    "font_family": "Shree-Lipi",
    "variants": ["Shree-Dev-0714", "Shree-Dev-0702"],
    "encoding": "custom",
    "mappings": {
      "¹": "क",
      "º": "ख",
      ...
    },
    "ligatures": {
      "Œ": "क्ष",
      ...
    }
  }
  ```

#### 5. Unicode Converter
- Apply mapping tables to raw text
- Handle multi-character sequences (matras, conjuncts)
- Normalize Unicode output (NFC normalization)

#### 6. Translation Engine
- Abstraction layer supporting multiple backends
- Chunking logic for large documents
- Retry logic for API failures
- Rate limiting for cloud APIs

#### 7. Output Generator
- Plain text with encoding metadata header
- Markdown with proper formatting
- PDF reconstruction (using ReportLab or similar)

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | Rich PDF libraries, easy distribution |
| PDF Parsing | PyMuPDF | Fast, reliable, good font extraction |
| CLI Framework | Click or Typer | Modern, type-hinted CLI |
| GUI (optional) | PyQt6 or Tkinter | Cross-platform desktop GUI |
| Local LLM | Ollama Python SDK | Privacy-preserving translation |
| Cloud Translation | googletrans / deepl-python | Fallback for quality |
| Packaging | PyInstaller | Single executable distribution |
| Config | TOML | Human-readable configuration |

---

## Data Model

### Input Document Model

```python
@dataclass
class PDFDocument:
    filepath: Path
    pages: List[PDFPage]
    metadata: DocumentMetadata

@dataclass
class PDFPage:
    page_number: int
    text_blocks: List[TextBlock]

@dataclass
class TextBlock:
    raw_text: str
    font_name: Optional[str]
    font_size: float
    position: BoundingBox
    detected_encoding: Optional[str]
    unicode_text: Optional[str]
```

### Encoding Detection Result

```python
@dataclass
class EncodingDetectionResult:
    detected_encoding: str  # e.g., "shree-lipi-0714"
    confidence: float  # 0.0 to 1.0
    method: str  # "font_match" | "heuristic" | "user_override"
    fallback_encodings: List[str]
```

### Translation Result

```python
@dataclass
class TranslationResult:
    source_text: str  # Unicode
    translated_text: str
    source_language: str
    target_language: str
    translation_backend: str
    warnings: List[str]
```

---

## User Interface Design

### CLI Interface

```bash
# Basic usage (auto-detect everything)
legacylipi translate input.pdf -o output.txt

# Specify target language
legacylipi translate input.pdf -o output.md --target-lang english

# Force specific encoding
legacylipi translate input.pdf --encoding shree-lipi-0714

# Use local LLM for translation
legacylipi translate input.pdf --translator ollama --model llama3

# Just convert to Unicode (no translation)
legacylipi convert input.pdf -o unicode_output.txt

# Detect encoding only
legacylipi detect input.pdf

# List supported encodings
legacylipi encodings list

# Output with layout preservation
legacylipi translate input.pdf -o output.pdf --preserve-layout
```

### CLI Output Examples

#### Successful Processing
```
$ legacylipi translate maharashtra_act.pdf -o translated.md

LegacyLipi v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Input: maharashtra_act.pdf (11 pages)

🔍 Analyzing document...
   Pages 1-2: Unicode Marathi (Devanagari) ✓
   Pages 3-11: Legacy encoding detected

🎯 Encoding Detection:
   Font: Shree-Dev-0714
   Confidence: 97.3%
   Method: font_name_match

🔄 Converting to Unicode...
   ████████████████████████████████████████ 100%
   Converted 11 pages successfully

🌐 Translating to English...
   Using: Google Translate API
   ████████████████████████████████████████ 100%

✅ Complete!
   Output: translated.md
   Source language: Marathi
   Target language: English

📊 Summary:
   - Characters processed: 45,230
   - Words translated: 7,845
   - Processing time: 23.4s
```

#### Detection-Only Mode
```
$ legacylipi detect sample.pdf

LegacyLipi v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Analyzing: sample.pdf

Page-by-Page Analysis:
┌─────────┬────────────────────┬────────────────┬────────────┐
│ Page    │ Detected Encoding  │ Confidence     │ Font Name  │
├─────────┼────────────────────┼────────────────┼────────────┤
│ 1-2     │ Unicode (Marathi)  │ 100%           │ Mangal     │
│ 3-11    │ Shree-Lipi-0714    │ 97%            │ Shree-Dev  │
└─────────┴────────────────────┴────────────────┴────────────┘

Recommendation: Use --encoding shree-lipi-0714 for pages 3-11
```

### GUI Mockup (P1)

```
┌─────────────────────────────────────────────────────────────────┐
│  LegacyLipi - PDF Translator                              [─][□][×] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │              Drag and drop PDF here                         │ │
│  │                    or click to browse                       │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Selected: maharashtra_act.pdf                                   │
│                                                                   │
│  ┌─ Encoding ─────────────────────────────────────────────────┐  │
│  │ ○ Auto-detect (recommended)                                │  │
│  │ ○ Manual: [Shree-Lipi-0714        ▼]                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─ Translation ──────────────────────────────────────────────┐  │
│  │ Target Language: [English              ▼]                  │  │
│  │ Backend:         [Google Translate     ▼]                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─ Output ───────────────────────────────────────────────────┐  │
│  │ Format: ○ Text  ● Markdown  ○ PDF                          │  │
│  │ □ Include intermediate Unicode file                        │  │
│  │ □ Side-by-side bilingual output                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Processing... Page 5/11                                    │  │
│  │ ████████████████████░░░░░░░░░░░░░░░░░░░░ 45%               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│                              [  Translate  ]                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Encoding Detection Algorithm

### Step 1: Extract Font Metadata

```python
def extract_font_info(pdf_path: Path) -> List[FontInfo]:
    """Extract all font names and properties from PDF."""
    doc = fitz.open(pdf_path)
    fonts = set()
    for page in doc:
        for font in page.get_fonts():
            fonts.add(FontInfo(
                name=font[3],  # Font name
                encoding=font[4],  # Encoding
                is_embedded=font[5]
            ))
    return list(fonts)
```

### Step 2: Font Name Matching

```python
# Priority-ordered list of legacy font patterns
LEGACY_FONT_PATTERNS = {
    r"shree.*dev.*07(14|02|05)": "shree-lipi",
    r"kruti.*dev": "kruti-dev",
    r"aps.*dv": "aps-dv",
    r"chanakya": "chanakya",
    r"walkman.*chanakya": "walkman-chanakya",
    r"dvb.*tt": "dvb-tt",
    r"shusha": "shusha",
}

def match_font_name(font_name: str) -> Optional[str]:
    """Match font name against known legacy patterns."""
    font_lower = font_name.lower()
    for pattern, encoding in LEGACY_FONT_PATTERNS.items():
        if re.search(pattern, font_lower):
            return encoding
    return None
```

### Step 3: Heuristic Detection (Fallback)

When font metadata is unavailable or inconclusive:

```python
def heuristic_detect(text: str) -> EncodingDetectionResult:
    """
    Analyze character distribution to detect encoding.

    Legacy encodings have specific patterns:
    - High frequency of certain Latin characters (¹, º, », etc.)
    - Absence of Unicode Devanagari range (0900-097F)
    - Specific character sequences unique to each font
    """

    # Check for Unicode Devanagari
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    if devanagari_count > len(text) * 0.3:
        return EncodingDetectionResult("unicode-devanagari", 1.0, "heuristic")

    # Check for legacy font signatures
    signatures = {
        "shree-lipi": ["´Ö", "Æü", "Ö¸ü", "ü®Ö"],
        "kruti-dev": ["d`fr", "Hkkjr"],
        "chanakya": ["Ñfr", "ns'k"],
    }

    for encoding, patterns in signatures.items():
        matches = sum(1 for p in patterns if p in text)
        if matches >= 2:
            confidence = min(0.95, 0.7 + (matches * 0.1))
            return EncodingDetectionResult(encoding, confidence, "heuristic")

    return EncodingDetectionResult("unknown", 0.0, "heuristic")
```

### Step 4: Confidence Scoring

```python
def calculate_confidence(
    font_match: Optional[str],
    heuristic_match: Optional[str],
    sample_conversion_success: float
) -> Tuple[str, float]:
    """
    Combine multiple signals for final encoding decision.

    Returns (encoding, confidence)
    """
    if font_match and heuristic_match and font_match == heuristic_match:
        return (font_match, 0.98)
    elif font_match:
        return (font_match, 0.90)
    elif heuristic_match:
        return (heuristic_match, 0.75)
    else:
        return ("unknown", 0.0)
```

---

## Mapping Table Format

### Standard Mapping File Structure

```yaml
# shree-lipi-0714.yaml
metadata:
  font_family: "Shree-Lipi"
  variant: "0714"
  language: "Marathi"
  script: "Devanagari"
  version: "1.0"
  contributors:
    - "LegacyLipi Team"

# Direct character mappings (legacy -> unicode)
mappings:
  # Vowels
  "†": "अ"
  "‡": "आ"
  "ˆ": "इ"
  "‰": "ई"
  # ... continues

  # Consonants
  "¹": "क"
  "º": "ख"
  "»": "ग"
  "¼": "घ"
  # ... continues

  # Matras (vowel signs)
  "Ö": "ा"  # aa matra
  "ß": "ि"  # i matra
  "ß": "ी"  # ii matra
  # ... continues

# Multi-character sequences (order matters - process longest first)
ligatures:
  "Œ": "क्ष"
  "¡": "त्र"
  "–": "ज्ञ"
  "Âü": "श्र"
  # ... continues

# Half-character mappings
half_forms:
  "Ûú": "क्"
  "Üú": "क्क"
  # ... continues

# Special handling rules
rules:
  - type: "reorder_matra"
    description: "Reorder pre-base matras to post-base position"
  - type: "normalize_nukta"
    description: "Combine nukta with base consonant"
```

### Mapping Table Sources

1. **Existing converters:** Reverse-engineer from tools like:
   - Baraha (has multiple legacy font support)
   - Google's Indic Input Tools
   - Microsoft's legacy converters

2. **Font analysis:** Direct inspection of legacy font files to extract glyph mappings

3. **Community contributions:** Open format allows crowdsourced mappings

4. **Manual creation:** For less common fonts, manual mapping with native speaker verification

---

## Error Handling

### Error Categories

| Code | Category | Example | User Action |
|------|----------|---------|-------------|
| E001 | Input Error | File not found | Check file path |
| E002 | Input Error | Not a valid PDF | Ensure file is PDF |
| E003 | Input Error | Password protected | Provide password |
| E010 | Detection Error | Unknown encoding | Use --encoding flag |
| E011 | Detection Error | Low confidence | Review suggestion, override if needed |
| E020 | Conversion Error | Missing mapping | Report to maintainers |
| E021 | Conversion Error | Ambiguous character | Check output, may need manual review |
| E030 | Translation Error | API rate limit | Wait and retry |
| E031 | Translation Error | API authentication | Check API key |
| E032 | Translation Error | Network error | Check internet connection |
| E040 | Output Error | Cannot write file | Check permissions |

### Error Message Format

```
❌ Error E010: Unknown Encoding

Unable to detect the font encoding for pages 3-11.

Font name found: "CustomFont-Regular"

Suggestions:
  1. Try specifying encoding manually:
     legacylipi translate input.pdf --encoding shree-lipi-0714

  2. List available encodings:
     legacylipi encodings list

  3. If you know the font family, search:
     legacylipi encodings search "font name"

Need help? File an issue: https://github.com/biswasbiplob/legacylipi/issues
```

---

## Testing Strategy

### Unit Tests

| Component | Test Focus |
|-----------|------------|
| PDF Parser | Various PDF versions, edge cases |
| Encoding Detector | Each supported font family |
| Unicode Converter | Character mapping accuracy |
| Translation Engine | API mocking, error handling |
| Output Generator | Format correctness |

### Integration Tests

- End-to-end processing of sample documents
- Multi-encoding documents (mixed Unicode + legacy)
- Large document handling (100+ pages)

### Test Data

Curate a test corpus including:
- Sample documents in each supported legacy encoding
- Government documents (with permission)
- Synthetically generated test PDFs
- Edge cases (empty pages, images-only pages, etc.)

### Accuracy Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Encoding detection accuracy | >95% | Against labeled test set |
| Character conversion accuracy | >99% | Character-by-character comparison |
| End-to-end translation readability | >90% | Human evaluation score |

---

## Release Plan

### Phase 1: MVP (v0.1) - 4 weeks
- CLI tool with basic functionality
- Support for 5 most common encodings (Shree-Lipi, Kruti Dev, APS, Chanakya, DVB)
- Text output only
- Google Translate integration
- Windows + Linux support

### Phase 2: Enhanced (v0.5) - 4 weeks
- GUI application
- 15+ encoding support
- Markdown output
- Ollama local translation
- macOS support
- Confidence scoring and warnings

### Phase 3: Production (v1.0) - 4 weeks
- PDF output with layout preservation
- 30+ encoding support
- Plugin architecture for new encodings
- Side-by-side output
- Comprehensive documentation
- PyPI package

### Phase 4: Community (v1.x) - Ongoing
- Open source release
- Community-contributed mappings
- Additional language support (Tamil, Telugu, etc.)
- Web interface (optional)

---

## Success Metrics

### Quantitative

| Metric | Target | Measurement |
|--------|--------|-------------|
| Encoding detection accuracy | >95% | Automated test suite |
| Processing speed | <10s per page | Benchmark suite |
| User-reported conversion errors | <1% | Issue tracker |
| Supported encodings | 50+ | Font family count |

### Qualitative

| Metric | Target | Measurement |
|--------|--------|-------------|
| User satisfaction | >4.0/5.0 | Post-use survey |
| Documentation completeness | >90% | Coverage audit |
| Installation success rate | >95% | First-time user survey |

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Incomplete mapping tables | High | Medium | Start with most common fonts; community contributions |
| PDF parsing edge cases | Medium | High | Use mature library (PyMuPDF); extensive test corpus |
| Translation API costs | Low | Medium | Support local LLM; chunking to reduce calls |
| Legal issues with font mappings | Medium | Low | Research fair use; create original mappings |
| Low adoption | Medium | Medium | Target specific user groups; good documentation |

---

## Open Questions

1. **Font licensing:** Can we legally distribute mapping tables derived from proprietary font analysis?

2. **OCR fallback:** Should we include OCR as a fallback for image-based PDFs?

3. **Batch processing:** Should v1.0 support directory/batch processing, or keep it simple?

4. **Cloud service:** Is there demand for a hosted web version, or is local-only sufficient?

5. **Enterprise features:** Should we plan for enterprise features (API, bulk processing, audit logs)?

---

## Appendix A: Supported Legacy Font Families

### Priority 0 (MVP)
1. **Shree-Lipi** - Most common in Maharashtra government
2. **Kruti Dev** - Popular in Hindi-speaking regions
3. **APS** - Common in publishing
4. **Chanakya** - Used in DTP industry
5. **DVB-TT** - Government of India standard

### Priority 1 (v0.5)
6. Walkman Chanakya
7. Shusha
8. DV-TTYogesh
9. Agra
10. Akruti
11. Bhasha
12. Sanskrit 2003
13. Aparajita
14. Kokila

### Priority 2 (v1.0+)
15. Tamil legacy fonts (e.g., TAU, TSCII)
16. Telugu legacy fonts
17. Kannada legacy fonts
18. Malayalam legacy fonts
19. Gujarati legacy fonts
20. Bengali/Bangla legacy fonts

---

## Appendix B: References

1. Unicode Technical Note #43: "Encoding Conversion between Legacy Hindi Fonts and Unicode"
2. Government of India "Multilingual Computing" guidelines
3. Baraha software documentation
4. W3C Internationalization documentation for Devanagari
5. Unicode Standard Chapter 12: South and Central Asian Scripts

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Legacy encoding** | Non-Unicode character encoding that maps regional scripts to ASCII/Latin code points |
| **Matra** | Vowel sign attached to consonants in Devanagari |
| **Conjunct** | Combined form of multiple consonants (ligature) |
| **Nukta** | Diacritical mark in Devanagari for borrowed sounds |
| **Devanagari** | Script used for Hindi, Marathi, Sanskrit, and other Indian languages |
| **Shree-Lipi** | Popular legacy font family for Devanagari, widely used in Maharashtra |
| **NFC Normalization** | Unicode Normalization Form Composed - standard form for text |

---

*Document End*
