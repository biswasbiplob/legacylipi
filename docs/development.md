# Development Guide

Guide for contributing to LegacyLipi development.

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

```bash
# Clone the repository
git clone https://github.com/biswasbiplob/legacylipi.git
cd legacylipi

# Install all dependencies (including dev)
uv sync --all-extras
```

## Running Tests

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

## Code Quality

```bash
# Run linter
uv run ruff check src/ tests/

# Run linter with auto-fix
uv run ruff check --fix src/ tests/

# Run type checker
uv run mypy src/legacylipi/
```

## Project Structure

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
│   ├── translator.py        # Translation backends
│   ├── output_generator.py  # Text/Markdown/PDF output generation
│   └── utils/
│       └── usage_tracker.py # API usage tracking with monthly limits
├── mappings/
│   └── loader.py            # Font mapping tables
├── ui/
│   └── app.py               # NiceGUI web interface
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

## Adding a New Encoding

### 1. Add Mapping to loader.py

Add your character mappings to `src/legacylipi/mappings/loader.py`:

```python
# Define your mapping dictionaries
MY_FONT_MAPPINGS = {
    "a": "अ",
    "b": "ब",
    # ... more character mappings
}

MY_FONT_LIGATURES = {
    "ksh": "क्ष",
    # ... ligature mappings
}

# Add to BUILTIN_MAPPINGS dict at the bottom of the file
BUILTIN_MAPPINGS: dict[str, MappingTable] = {
    # ... existing mappings ...
    "my-font": MappingTable(
        encoding_name="my-font",
        font_family="My Font",
        language="Hindi",
        script="Devanagari",
        mappings=MY_FONT_MAPPINGS,
        ligatures=MY_FONT_LIGATURES,
        variants=["MyFont-Regular", "MyFont-Bold"],
    ),
}
```

### 2. Add Font Detection Pattern

Add font name patterns to `src/legacylipi/core/encoding_detector.py`:

```python
LegacyFontPattern(
    encoding_name="my-font",
    patterns=[r"my[-_]font", r"myfont"],
    signatures=["unique", "text", "signatures"],
    priority=5,
)
```

### 3. Add Tests

Create tests for the new encoding to verify:
- Font detection works
- Character mapping is correct
- Ligatures and half-forms are handled

## Making a Release

```bash
# Update version in pyproject.toml and __init__.py
# Then:
uv build
uv publish  # (when ready for PyPI)
```

## Common Development Tasks

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
