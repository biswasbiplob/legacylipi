# LegacyLipi UI Upgrade Plan

## Overview

Migrate the LegacyLipi web UI from a monolithic NiceGUI Python app (`src/legacylipi/ui/app.py`, ~1140 lines) to a decoupled architecture: a **FastAPI REST API** backend serving a **React + TypeScript** frontend. The existing core pipeline (`src/legacylipi/core/`) remains completely untouched.

### Why Migrate?

| Problem (NiceGUI) | Solution (React + FastAPI) |
|---|---|
| Python-rendered HTML, limited responsiveness | Tailwind CSS responsive-first design |
| Tight coupling between UI and business logic | Clean API boundary, reusable endpoints |
| Limited component ecosystem | shadcn/ui + React ecosystem (1000s of components) |
| No mobile support | Mobile-first responsive layout |
| Hard to test UI in isolation | Component tests + E2E tests with Playwright |
| No API for external integrations | RESTful API available for CLI tools, scripts, etc. |

---

## Technology Stack

### Backend: FastAPI

| Choice | Reasoning |
|---|---|
| **FastAPI** | Async-native (matches existing `async` pipeline), automatic OpenAPI docs, Pydantic validation, built-in SSE support |
| **Uvicorn** | ASGI server, production-ready |
| **python-multipart** | Required for file upload handling in FastAPI |

### Frontend: React 19 + Vite + TypeScript

| Choice | Reasoning |
|---|---|
| **React 19** | Largest ecosystem, best file upload libraries (react-dropzone), PDF preview (react-pdf), most component libraries |
| **Vite** | Fast HMR, simple config, no SSR complexity (not needed — single page app, no SEO) |
| **TypeScript** | Type safety matching Python's type hints, catch errors at build time |
| **Tailwind CSS v4** | Utility-first responsive design, dark mode support, zero runtime overhead |
| **shadcn/ui** | Beautiful, accessible, production-ready components (copy-pasted, no runtime dependency) |

### Why Not Next.js / Vue / Svelte?

- **Next.js**: Adds SSR complexity we don't need. This is a single-page form app with no SEO requirements. Vite is simpler.
- **Vue.js**: Good option, but React has a larger ecosystem for file-heavy apps (react-dropzone, react-pdf) and the most polished component library (shadcn/ui).
- **Svelte**: Smallest ecosystem for file upload/preview. Limited component library options.

---

## Architecture

```
                    Browser (React SPA)
                         │
              ┌──────────┼──────────┐
              │     HTTP/SSE        │
              │                     │
         FastAPI REST API           │
         (port 8000)                │
              │                     │
    ┌─────────┼─────────┐          │
    │         │         │          │
 Sessions  Pipeline  Progress      │
 Manager   Runner    (SSE)        │
    │         │                    │
    │    ┌────┼────┐               │
    │    │    │    │               │
    │  Core Pipeline (unchanged)   │
    │  ├─ pdf_parser.py            │
    │  ├─ ocr_parser.py            │
    │  ├─ encoding_detector.py     │
    │  ├─ unicode_converter.py     │
    │  ├─ translator.py            │
    │  └─ output_generator.py      │
    │                              │
    └── In-Memory Session Store    │
        (file bytes + results)     │
                                   │
              Static Files ────────┘
              (frontend/dist/)
```

### Key Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Progress reporting | **SSE** (not WebSocket) | Unidirectional (server→client), auto-reconnect via `EventSource`, works through proxies, simpler than WebSocket |
| Session storage | **In-memory dict with TTL** | Matches current NiceGUI pattern (per-client state in memory). Switch to Redis if multi-process scaling needed |
| Background processing | **FastAPI BackgroundTasks** | Pipeline is already async-first. No need for Celery/RQ for a single-process tool |
| Static file serving | **FastAPI serves `frontend/dist/`** | Single process, single port, single command. Add Nginx/CDN later if needed |
| NiceGUI backward compat | **Keep deprecated for 1 release** | `legacylipi-ui` entry point continues to work. Remove in v0.9.0 |

---

## API Design

Base URL: `/api/v1`

### 1. Health & Configuration

```
GET /api/v1/health
  → { "status": "ok", "version": "0.8.0" }

GET /api/v1/config/languages
  → { "target": {"en": "English", "hi": "Hindi", ...}, "ocr": {"mar": "Marathi", ...} }

GET /api/v1/config/translators
  → { "backends": {"trans": "Translate-Shell (CLI)", ...}, "openai_models": [...], "ollama_models": [...] }

GET /api/v1/config/options
  → { "output_formats": {...}, "translation_modes": {...}, "workflow_modes": {...}, "ocr_engines": {...} }
```

### 2. Session Management

```
POST /api/v1/sessions/upload
  Content-Type: multipart/form-data
  Body: file=<PDF binary>
  → { "session_id": "uuid", "filename": "doc.pdf", "file_size": 310000 }

DELETE /api/v1/sessions/{session_id}
  → { "status": "deleted" }
```

### 3. Processing Pipelines

```
POST /api/v1/sessions/{session_id}/scan-copy
  Body: { "dpi": 300, "color_mode": "color", "quality": 85 }
  → { "job_id": "uuid" }

POST /api/v1/sessions/{session_id}/convert
  Body: { "ocr_engine": "easyocr", "ocr_lang": "mar", "ocr_dpi": 300, "output_format": "pdf" }
  → { "job_id": "uuid" }

POST /api/v1/sessions/{session_id}/translate
  Body: {
    "target_lang": "en",
    "output_format": "pdf",
    "translation_mode": "structure_preserving",
    "translator": "trans",
    "use_ocr": false,
    "ocr_engine": "easyocr",
    "ocr_lang": "mar",
    "ocr_dpi": 300,
    // Translator-specific (optional)
    "openai_key": null,
    "openai_model": "gpt-4o-mini",
    "ollama_model": "llama3.2",
    "ollama_host": "http://localhost:11434",
    "trans_path": null,
    "gcp_project": null
  }
  → { "job_id": "uuid" }
```

### 4. Progress Monitoring (SSE)

```
GET /api/v1/sessions/{session_id}/progress
  Accept: text/event-stream

  Events:
    data: {"status": "processing", "percent": 15, "step": "parsing", "message": "Parsing PDF..."}
    data: {"status": "processing", "percent": 40, "step": "translating", "message": "Translating block 5/20..."}
    data: {"status": "complete", "filename": "translated_doc.pdf", "file_size": 45000}
    data: {"status": "error", "message": "Translation failed: rate limited", "details": "..."}
```

### 5. Result Download

```
GET /api/v1/sessions/{session_id}/download
  → Binary file with Content-Disposition header
```

### Pydantic Schemas

```python
# Request schemas
class ScanCopyRequest(BaseModel):
    dpi: int = 300
    color_mode: Literal["color", "grayscale", "bw"] = "color"
    quality: int = Field(85, ge=1, le=100)

class ConvertRequest(BaseModel):
    ocr_engine: Literal["easyocr", "tesseract"] = "easyocr"
    ocr_lang: str = "mar"
    ocr_dpi: int = 300
    output_format: Literal["pdf", "text", "markdown"] = "pdf"

class TranslateRequest(BaseModel):
    target_lang: str = "en"
    output_format: Literal["pdf", "text", "markdown"] = "pdf"
    translation_mode: Literal["structure_preserving", "flowing"] = "structure_preserving"
    translator: str = "trans"
    use_ocr: bool = False
    ocr_engine: Literal["easyocr", "tesseract"] = "easyocr"
    ocr_lang: str = "mar"
    ocr_dpi: int = 300
    openai_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3.2"
    ollama_host: str = "http://localhost:11434"
    trans_path: str | None = None
    gcp_project: str | None = None

# Response schemas
class UploadResponse(BaseModel):
    session_id: str
    filename: str
    file_size: int

class ProgressEvent(BaseModel):
    status: Literal["processing", "complete", "error"]
    percent: int = 0
    step: str = ""
    message: str = ""
    filename: str | None = None
    file_size: int | None = None
```

---

## Frontend Architecture

### Component Tree

```
App
├── Header (logo, title, version badge)
├── MainLayout (2-column responsive → single column on mobile)
│   ├── SettingsPanel (left column)
│   │   ├── FileUploader (drag-drop zone, file info display)
│   │   ├── WorkflowModeSelector (radio group: Scan/Convert/Translate)
│   │   ├── ScanCopySettings [if scan_copy] (DPI, color mode, quality slider)
│   │   ├── OcrSettings [if convert|translate] (engine, language, DPI)
│   │   ├── OutputFormatSelect [if convert|translate]
│   │   ├── TranslationSettings [if translate] (target language, mode)
│   │   ├── TranslatorSettings [if translate] (backend + dynamic sub-forms)
│   │   │   ├── OpenAIOptions (API key, model select)
│   │   │   ├── OllamaOptions (model, host URL)
│   │   │   ├── TransShellOptions (binary path)
│   │   │   └── GCPOptions (project ID)
│   │   └── ActionButton (dynamic label/icon per workflow mode)
│   │
│   └── StatusPanel (right column)
│       ├── IdleState (instructions per workflow mode)
│       ├── ProgressState (progress bar, step label, %, message)
│       ├── CompleteState (success icon, file info, download button)
│       └── ErrorState (error message, retry button)
│
└── Footer (links, version)
```

### State Management

React Context + `useReducer`. Appropriate because state is localized to a single page (no complex routing needed).

```typescript
interface AppState {
  // Session
  sessionId: string | null;
  uploadedFilename: string | null;
  uploadedFileSize: number | null;

  // Workflow
  workflowMode: 'scan_copy' | 'convert' | 'translate';

  // Processing state
  processingStatus: 'idle' | 'processing' | 'complete' | 'error';
  progress: number;          // 0-100
  progressStep: string;      // "parsing", "detecting", etc.
  progressMessage: string;
  errorMessage: string | null;

  // Result
  resultFilename: string | null;
  resultFileSize: number | null;

  // Settings (mirrors TranslationUI.__init__ from app.py)
  targetLang: string;
  outputFormat: string;
  useOcr: boolean;
  ocrEngine: string;
  ocrLang: string;
  ocrDpi: number;
  translator: string;
  translationMode: string;
  openaiKey: string;
  openaiModel: string;
  ollamaModel: string;
  ollamaHost: string;
  transPath: string;
  gcpProject: string;
  scanDpi: number;
  scanColorMode: string;
  scanQuality: number;
}
```

### Custom Hooks

| Hook | Purpose |
|---|---|
| `useConfig()` | Fetches config from `/api/v1/config/*` on mount, caches in state |
| `useFileUpload()` | Handles drag-drop + file upload via API, returns `sessionId` |
| `useProgress(sessionId)` | Subscribes to SSE stream, dispatches progress updates to context |
| `useProcessing(sessionId)` | POSTs to processing endpoint, starts progress listener |
| `useDownload(sessionId)` | Fetches blob from download endpoint, triggers browser download |

### Styling

- **Tailwind CSS v4** utility classes for responsive layout
- **shadcn/ui** components: Button, Card, Select, Slider, RadioGroup, Progress, Input, Label, Separator
- **Dark mode default** (matching current NiceGUI behavior with `ui.dark_mode().enable()`)
- **Light/dark toggle** in header
- **Responsive breakpoints**: 2 columns on `md:` (768px+), single column below

---

## Project Structure

```
legacylipi/
├── src/legacylipi/
│   ├── core/                        # UNCHANGED
│   ├── mappings/                    # UNCHANGED
│   ├── ui/                          # DEPRECATED (keep for backward compat)
│   │   └── app.py                   # Add deprecation warning
│   ├── api/                         # NEW — FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, lifespan, CORS, static mount
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── session_manager.py       # In-memory session store with TTL cleanup
│   │   ├── pipeline.py              # Async pipeline runner (extracted from app.py)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── config.py            # GET /config/* endpoints
│   │       ├── sessions.py          # POST upload, DELETE session
│   │       ├── processing.py        # POST scan-copy/convert/translate
│   │       ├── progress.py          # GET SSE progress stream
│   │       └── download.py          # GET file download
│   ├── cli.py                       # UPDATE: add `api` subcommand
│   └── __init__.py
│
├── frontend/                        # NEW — React frontend
│   ├── package.json
│   ├── vite.config.ts               # Vite config with API proxy
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css                # Tailwind directives
│       ├── components/
│       │   ├── ui/                  # shadcn/ui components (Button, Card, etc.)
│       │   ├── Header.tsx
│       │   ├── FileUploader.tsx
│       │   ├── WorkflowModeSelector.tsx
│       │   ├── ScanCopySettings.tsx
│       │   ├── OcrSettings.tsx
│       │   ├── OutputFormatSelect.tsx
│       │   ├── TranslationSettings.tsx
│       │   ├── TranslatorSettings.tsx
│       │   ├── ActionButton.tsx
│       │   └── StatusPanel.tsx
│       ├── hooks/
│       │   ├── useFileUpload.ts
│       │   ├── useProgress.ts
│       │   ├── useProcessing.ts
│       │   ├── useDownload.ts
│       │   └── useConfig.ts
│       ├── context/
│       │   └── AppContext.tsx
│       └── lib/
│           ├── api.ts               # Typed fetch wrapper
│           ├── constants.ts         # Mirrors Python constants
│           └── types.ts             # TypeScript interfaces
│
├── tests/
│   ├── ...existing tests...
│   ├── test_api.py                  # NEW — FastAPI endpoint tests
│   └── test_api_integration.py      # NEW — Full pipeline API tests
│
└── scripts/
    ├── check.sh                     # UPDATE: add frontend checks
    └── dev.sh                       # NEW — Start both backend + frontend
```

---

## Implementation Phases

### Phase 1: Backend API Foundation

**Goal**: Build the FastAPI layer that wraps the existing core pipeline.

| Step | Task | Key Files |
|---|---|---|
| 1.1 | Add `fastapi`, `uvicorn[standard]`, `python-multipart` to `pyproject.toml` dependencies | `pyproject.toml` |
| 1.2 | Create session manager with TTL-based cleanup | `src/legacylipi/api/session_manager.py` |
| 1.3 | Create Pydantic request/response schemas | `src/legacylipi/api/schemas.py` |
| 1.4 | Create config routes (extract constants from `app.py`) | `src/legacylipi/api/routes/config.py` |
| 1.5 | Create upload/session routes | `src/legacylipi/api/routes/sessions.py` |
| 1.6 | Extract pipeline runner from `TranslationUI._translate()` into standalone async functions | `src/legacylipi/api/pipeline.py` |
| 1.7 | Create processing routes (scan-copy, convert, translate) | `src/legacylipi/api/routes/processing.py` |
| 1.8 | Create SSE progress endpoint | `src/legacylipi/api/routes/progress.py` |
| 1.9 | Create download route | `src/legacylipi/api/routes/download.py` |
| 1.10 | Create FastAPI app with CORS, lifespan, router registration | `src/legacylipi/api/main.py` |
| 1.11 | Add API tests (httpx AsyncClient) | `tests/test_api.py` |

**Pipeline Extraction** (Step 1.6 — most critical):

The `TranslationUI._translate()` method (app.py lines 719-1110) contains the entire pipeline orchestration. Extract into three standalone async functions:

```python
# pipeline.py
async def run_scan_copy(file_bytes: bytes, config: ScanCopyRequest, progress_callback) -> bytes
async def run_convert(file_bytes: bytes, config: ConvertRequest, progress_callback) -> tuple[bytes, str]
async def run_translate(file_bytes: bytes, config: TranslateRequest, progress_callback) -> tuple[bytes, str]
```

Each function:
- Accepts parameters (not UI state)
- Reports progress via an async callback (not queue-based UI updates)
- Returns result bytes + filename
- Runs blocking operations (PDF parsing, OCR) in `asyncio.get_event_loop().run_in_executor()`

### Phase 2: Frontend Scaffold

**Goal**: Set up the React project with Tailwind + shadcn/ui.

| Step | Task |
|---|---|
| 2.1 | Initialize React project: `npm create vite@latest frontend -- --template react-ts` |
| 2.2 | Install Tailwind CSS v4: `npm install -D tailwindcss @tailwindcss/vite` |
| 2.3 | Install shadcn/ui: `npx shadcn@latest init` then add components |
| 2.4 | Configure Vite proxy to `localhost:8000` for API calls |
| 2.5 | Create TypeScript types matching Pydantic schemas |
| 2.6 | Create typed API client (`lib/api.ts`) |

**Vite Proxy Config**:
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
})
```

### Phase 3: Frontend Components

**Goal**: Build all UI components bottom-up.

| Step | Component | Notes |
|---|---|---|
| 3.1 | `AppContext.tsx` | State reducer with actions: SET_FILE, SET_WORKFLOW_MODE, UPDATE_SETTINGS, SET_PROGRESS, SET_COMPLETE, SET_ERROR, RESET |
| 3.2 | Custom hooks | `useConfig`, `useFileUpload`, `useProgress`, `useProcessing`, `useDownload` |
| 3.3 | `Header.tsx` | Logo, title, dark/light toggle |
| 3.4 | `FileUploader.tsx` | Drag-drop zone with file info |
| 3.5 | `WorkflowModeSelector.tsx` | Radio group with mode descriptions |
| 3.6 | `ScanCopySettings.tsx` | DPI select, color mode, quality slider |
| 3.7 | `OcrSettings.tsx` | Engine select, language, DPI |
| 3.8 | `OutputFormatSelect.tsx` | Format dropdown |
| 3.9 | `TranslationSettings.tsx` | Target language, translation mode |
| 3.10 | `TranslatorSettings.tsx` | Backend select + dynamic sub-forms (OpenAI, Ollama, etc.) |
| 3.11 | `ActionButton.tsx` | Dynamic label/icon per workflow mode |
| 3.12 | `StatusPanel.tsx` | 4 states: idle, progress, complete, error |
| 3.13 | `App.tsx` | Wire everything in 2-column layout with conditional rendering |

**Conditional Rendering** (replaces NiceGUI's `set_visibility()`):
```tsx
{workflowMode === 'scan_copy' && <ScanCopySettings />}
{(workflowMode === 'convert' || workflowMode === 'translate') && <OcrSettings />}
{workflowMode !== 'scan_copy' && <OutputFormatSelect />}
{workflowMode === 'translate' && <TranslationSettings />}
{workflowMode === 'translate' && <TranslatorSettings />}
```

### Phase 4: Integration & Polish

| Step | Task |
|---|---|
| 4.1 | Dark mode implementation (Tailwind `dark:` classes, default dark) |
| 4.2 | Responsive design (2-col on md:, single-col on mobile) |
| 4.3 | Error handling (API errors, network failures, SSE reconnection) |
| 4.4 | Production build: `frontend/dist/` served by FastAPI |
| 4.5 | E2E testing with Playwright (upload, process, download for all 3 modes) |

### Phase 5: Cleanup & Release

| Step | Task |
|---|---|
| 5.1 | Update `pyproject.toml` — add FastAPI deps, new entry points, bump to v0.8.0 |
| 5.2 | Add `legacylipi api` CLI subcommand |
| 5.3 | Update `scripts/check.sh` — add frontend lint, typecheck, test |
| 5.4 | Create `scripts/dev.sh` — start both servers for development |
| 5.5 | Add deprecation warning to `src/legacylipi/ui/app.py` |
| 5.6 | Update README.md and CLAUDE.md with new architecture |

---

## Migration Patterns

### Progress Reporting: Queue → SSE

**Before (NiceGUI)** — Queue-based polling at 100ms:
```python
# Producer (in _translate)
self._progress_queue.put((completed, total, progress))

# Consumer (timer)
def _poll_progress_updates(self):
    latest = self._progress_queue.get_nowait()
    self.progress_bar.set_value(progress)
```

**After (FastAPI + SSE)** — Async queue + streaming response:
```python
# Producer (in pipeline.py)
async def progress_callback(percent, step, message):
    await session.progress_queue.put(ProgressEvent(
        status="processing", percent=percent, step=step, message=message
    ))

# Consumer (SSE endpoint)
async def progress_stream(session_id: str):
    session = session_manager.get(session_id)
    while True:
        event = await session.progress_queue.get()
        yield f"data: {event.model_dump_json()}\n\n"
        if event.status in ("complete", "error"):
            break
```

### File Upload: NiceGUI → REST

**Before**: `ui.upload` stores bytes in `self.uploaded_file`
**After**: `POST /sessions/upload` stores bytes in session store, returns `session_id`

### Conditional UI: set_visibility → React conditional rendering

**Before**: `self.scan_copy_section.set_visibility(is_scan_copy)`
**After**: `{workflowMode === 'scan_copy' && <ScanCopySettings />}`

---

## Development Workflow

### Running in Development

```bash
# Terminal 1: Backend (port 8000, auto-reload)
uv run uvicorn legacylipi.api.main:app --reload --port 8000

# Terminal 2: Frontend (port 5173, Vite HMR, proxies /api to 8000)
cd frontend && npm run dev
```

Or use the convenience script:
```bash
./scripts/dev.sh  # Starts both, kills both on Ctrl+C
```

### Production Serving

```bash
# Build frontend
cd frontend && npm run build   # → frontend/dist/

# Run combined server (FastAPI serves static files + API)
uv run legacylipi api --port 8000
# OR
uv run uvicorn legacylipi.api.main:app --host 0.0.0.0 --port 8000
```

### Pre-Commit Checks (Updated)

```bash
./scripts/check.sh
# Runs:
# 1. ruff format --check (Python)
# 2. ruff check (Python)
# 3. mypy (Python)
# 4. pytest (Python, including API tests)
# 5. cd frontend && npm run lint (JS/TS)
# 6. cd frontend && npm run typecheck (TS)
# 7. cd frontend && npm test (Vitest)
```

---

## Dependency Changes

### Add to `pyproject.toml` dependencies

```toml
"fastapi>=0.115.0",
"uvicorn[standard]>=0.30.0",
"python-multipart>=0.0.9",
```

### Add new entry points

```toml
[project.scripts]
legacylipi = "legacylipi.cli:main"
legacylipi-ui = "legacylipi.ui.app:main"       # Keep (deprecated)
legacylipi-web = "legacylipi.api.main:serve"    # New
```

### Frontend dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "vitest": "^3.0.0",
    "@testing-library/react": "^16.0.0"
  }
}
```

### Eventually Remove (v0.9.0)

```toml
"nicegui>=2.0.0",   # Remove after deprecation period
```

---

## Testing Strategy

### Backend API Tests (`tests/test_api.py`)

Using `httpx.AsyncClient` with `ASGITransport` (no real server needed):

- **Session management**: Create, get, delete, TTL expiry
- **Upload**: Valid PDF → 200, non-PDF → 400, oversized → 413
- **Processing**: Start each workflow type, verify background task creation
- **SSE progress**: Verify event format, sequence (processing → complete), error events
- **Download**: Verify Content-Type, Content-Disposition, binary content
- **Error handling**: Invalid session → 404, processing while busy → 409

### Frontend Component Tests (Vitest + React Testing Library)

- Each component renders correctly with mock data
- `FileUploader` triggers upload on file drop
- `WorkflowModeSelector` shows/hides correct sections
- `StatusPanel` transitions between states
- `TranslatorSettings` shows correct sub-form per backend

### Frontend Hook Tests (Vitest)

- `useFileUpload` calls correct endpoint, handles errors
- `useProgress` parses SSE events correctly
- `useConfig` caches data after first fetch

### E2E Tests (Playwright)

- Full workflow: upload PDF → select scan copy → process → download
- Full workflow: upload PDF → convert with OCR → download
- Full workflow: upload PDF → translate with mock backend → download
- Responsive: verify single-column on mobile viewport
- Error recovery: simulate processing error, verify retry works

---

## Timeline Estimate

| Phase | Description | Effort |
|---|---|---|
| Phase 1 | Backend API Foundation | ~2-3 days |
| Phase 2 | Frontend Scaffold | ~0.5 day |
| Phase 3 | Frontend Components | ~2-3 days |
| Phase 4 | Integration & Polish | ~1-2 days |
| Phase 5 | Cleanup & Release | ~0.5 day |
| **Total** | | **~6-9 days** |

---

## Version Impact

- Bump version: `0.7.0` → `0.8.0` (new feature, backward compatible)
- `legacylipi-ui` continues to work (deprecated)
- `legacylipi-web` is the new recommended command
- All CLI commands remain unchanged
- Core pipeline entirely untouched
