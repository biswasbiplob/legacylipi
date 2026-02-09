# Development Guide

Guide for contributing to LegacyLipi development.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Node.js 20+ and npm (for frontend development)

## Setup

```bash
# Clone the repository
git clone https://github.com/biswasbiplob/legacylipi.git
cd legacylipi

# Install all Python dependencies (including dev)
uv sync --all-extras

# Install frontend dependencies
cd frontend && npm install && cd ..
```

## Running the Application

### Production mode (single server)

Builds the React frontend and serves it alongside the API:

```bash
# Build frontend first
cd frontend && npm run build && cd ..

# Start the combined server
uv run legacylipi api
# or
uv run legacylipi-web
```

Open http://localhost:8000 in your browser. The FastAPI server serves both the API and the built React static files.

### Development mode (hot-reload)

Run both servers with hot-reload for the fastest development experience:

```bash
./scripts/dev.sh
```

This starts:
- **FastAPI backend** at http://localhost:8000
- **Vite dev server** at http://localhost:5173 (with HMR, proxies `/api` requests to backend)

Open http://localhost:5173 for development. Changes to React components update instantly; changes to Python code require a backend restart.

You can also start each server individually:

```bash
# Backend only
uv run python -m legacylipi.api.main

# Frontend only (requires backend running)
cd frontend && npm run dev
```

### Legacy NiceGUI UI (deprecated)

```bash
uv run legacylipi ui
# Open http://localhost:8080
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py -v

# Run with coverage
uv run pytest --cov=src/legacylipi --cov-report=html

# Run only fast tests (exclude slow/integration)
uv run pytest -m "not slow"
```

### Frontend type checking

```bash
cd frontend && npx tsc --noEmit
```

## Code Quality

### Pre-commit Checks (Recommended)

Always run the pre-commit check script before committing:

```bash
./scripts/check.sh
```

This runs all checks that CI will run:
1. Code formatting (ruff format)
2. Linting (ruff check)
3. Type checking (mypy)
4. Python tests (pytest)
5. Frontend TypeScript check (tsc)

### Individual Commands

```bash
# Run linter
uv run ruff check src/ tests/

# Run linter with auto-fix
uv run ruff check --fix src/ tests/

# Run formatter
uv run ruff format src/

# Run type checker
uv run mypy src/legacylipi/
```

### CI Pipeline

The project uses GitHub Actions for CI. On every PR and push to main:
- Tests run on Python 3.12 and 3.13
- Linting and type checking are enforced
- Package build is verified

When a PR merges to main, a release is automatically created if the version in `pyproject.toml` has changed.

## Project Structure

```
legacylipi/
├── src/legacylipi/
│   ├── __init__.py              # Package exports
│   ├── cli.py                   # CLI interface (Click)
│   ├── api/                     # FastAPI REST API
│   │   ├── main.py              # App setup, CORS, static file serving
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── session_manager.py   # In-memory session store with TTL cleanup
│   │   ├── pipeline.py          # Async pipeline runners (scan-copy, convert, translate)
│   │   ├── deps.py              # Dependency injection (SessionManager)
│   │   └── routes/
│   │       ├── config.py        # GET /config/languages, /translators, /options
│   │       ├── sessions.py      # POST /sessions/upload, DELETE /sessions/{id}
│   │       ├── processing.py    # POST /sessions/{id}/scan-copy, /convert, /translate
│   │       ├── progress.py      # GET /sessions/{id}/progress (SSE stream)
│   │       └── download.py      # GET /sessions/{id}/download
│   ├── core/
│   │   ├── models.py            # Data models (PDFDocument, TextBlock, etc.)
│   │   ├── pdf_parser.py        # PDF parsing with PyMuPDF
│   │   ├── ocr_parser.py        # OCR-based PDF text extraction
│   │   ├── encoding_detector.py # Legacy font detection
│   │   ├── unicode_converter.py # Legacy-to-Unicode conversion
│   │   ├── translator.py        # Translation backends
│   │   ├── output_generator.py  # Text/Markdown/PDF output generation
│   │   ├── font_analyzer.py     # Font size analysis and normalization
│   │   └── utils/
│   │       ├── usage_tracker.py # API usage tracking with monthly limits
│   │       └── text_wrapper.py  # Text wrapping utilities for PDF generation
│   ├── mappings/
│   │   └── loader.py            # Font mapping tables
│   └── ui/
│       └── app.py               # NiceGUI web interface (deprecated)
│
├── frontend/                    # React + TypeScript frontend
│   ├── package.json
│   ├── vite.config.ts           # Vite config with Tailwind + API proxy
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx             # Entry point
│       ├── App.tsx              # Main layout
│       ├── index.css            # Tailwind CSS v4 + dark theme
│       ├── lib/
│       │   ├── types.ts         # TypeScript interfaces matching API schemas
│       │   ├── api.ts           # Typed fetch wrapper for all API endpoints
│       │   └── constants.ts     # Default values
│       ├── context/
│       │   └── AppContext.tsx    # React Context + useReducer state management
│       ├── hooks/
│       │   ├── useFileUpload.ts # File upload + session management
│       │   ├── useProgress.ts   # SSE progress streaming
│       │   ├── useProcessing.ts # Pipeline execution orchestration
│       │   ├── useDownload.ts   # Result file download
│       │   └── useConfig.ts     # Config loading on mount
│       └── components/
│           ├── Header.tsx
│           ├── FileUploader.tsx       # Drag-and-drop PDF upload
│           ├── WorkflowModeSelector.tsx
│           ├── ScanCopySettings.tsx
│           ├── OcrSettings.tsx
│           ├── OutputFormatSelect.tsx
│           ├── TranslationSettings.tsx
│           ├── TranslatorSettings.tsx
│           ├── ActionButton.tsx
│           └── StatusPanel.tsx        # Progress bar + download
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py              # FastAPI endpoint tests
│   ├── test_models.py
│   ├── test_pdf_parser.py
│   ├── test_ocr_parser.py
│   ├── test_encoding_detector.py
│   ├── test_unicode_converter.py
│   ├── test_mappings.py
│   ├── test_translator.py
│   ├── test_output_generator.py
│   ├── test_cli.py
│   └── test_integration.py
│
├── scripts/
│   ├── check.sh                 # Pre-commit checks (Python + frontend)
│   └── dev.sh                   # Start dev servers (backend + frontend)
│
├── docs/
│   ├── development.md           # This file
│   ├── cli-reference.md
│   ├── translation-backends.md
│   └── UIUpgradePlan.md         # Migration plan document
│
└── pyproject.toml               # Python project config + dependencies
```

## API Endpoints

The FastAPI backend exposes these endpoints (all under `/api/v1`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with version |
| GET | `/config/languages` | Available target + OCR languages |
| GET | `/config/translators` | Translation backends + model lists |
| GET | `/config/options` | Output formats, workflow modes, OCR engines |
| POST | `/sessions/upload` | Upload PDF, returns session ID |
| DELETE | `/sessions/{id}` | Delete session and cleanup |
| POST | `/sessions/{id}/scan-copy` | Start scan-copy pipeline |
| POST | `/sessions/{id}/convert` | Start convert pipeline |
| POST | `/sessions/{id}/translate` | Start translate pipeline |
| GET | `/sessions/{id}/progress` | SSE stream of progress events |
| GET | `/sessions/{id}/download` | Download result file |

Interactive API docs are available at http://localhost:8000/docs (Swagger UI) and http://localhost:8000/redoc (ReDoc).

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
# Update version in pyproject.toml (single source of truth)
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

# Add a frontend dependency
cd frontend && npm install package-name

# Build frontend for production
cd frontend && npm run build
```
