# LegacyLipi Improvement Opportunities

A prioritized list of improvements organized into three tiers: **Must-Have**, **Nice-to-Have**, and **Future Consideration**. Each item includes a description, rationale, complexity estimate, and relevant files.

---

## Must-Have Improvements

These address fundamental gaps in the core value proposition and should be shipped soon.

---

### 1. Complete Missing Encoding Mappings

**Description**: The encoding detector (`encoding_detector.py`, lines 82-148) defines patterns for `aps-dv`, `chanakya`, `walkman-chanakya`, `shusha`, `agra`, and `akruti` — but none of these have character mapping tables. The `BUILTIN_MAPPINGS` dict in `mappings/loader.py` only contains `shree-lipi`, `kruti-dev`, `dvb-tt`, and `shree-dev`. Users with these encodings see "encoding detected" but get garbled or no conversion.

**Why**: Users with Chanakya or APS-DV encoded documents (very common in Hindi government documents) cannot use LegacyLipi at all. This is the single biggest gap in the product.

**Complexity**: Medium per encoding (requires researching character mapping tables from reference converters)

**Files**:
- `src/legacylipi/mappings/` — add new mapping files (e.g., `chanakya.py`, `aps_dv.py`)
- `src/legacylipi/mappings/loader.py` — register new mappings in `BUILTIN_MAPPINGS`
- `src/legacylipi/core/encoding_detector.py` — verify detection patterns work correctly

---

### 2. Fix Translation Page Marker Corruption

**Description**: In flowing text mode, the CLI (`cli.py`, lines 352-357) concatenates all pages with `"--- Page N ---"` markers and translates the entire string as one request. Translation backends often corrupt or translate these markers (e.g., Google Translate turns `"--- Page 1 ---"` into `"--- pagina 1 ---"`). The output generator then fails to parse page boundaries correctly, causing all text to land on page 1.

**Why**: Page markers are a brittle contract between the translator and output generator. Corrupted markers produce completely wrong output structure.

**Fix**: Translate each page separately and reassemble after translation. This is more API calls but eliminates the marker problem entirely.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — change flowing-mode translation to per-page
- `src/legacylipi/ui/app.py` — same change in UI pipeline
- `src/legacylipi/core/output_generator.py` — simplify page-split logic (lines 1202-1256)

---

### 3. Source Language Auto-Detection

**Description**: The CLI defaults to `source_lang="mr"` (Marathi) and hardcodes this throughout (`cli.py` line 363). Hindi users with KrutiDev PDFs get poor translations because the system tells the backend the source is Marathi. The encoding-to-language mapping already exists in the `MappingTable.language` field — it just isn't used.

**Why**: Incorrect source language degrades translation quality significantly.

**Fix**: Map encoding → source language automatically: `shree-dev`/`shree-lipi`/`dvb-tt` → Marathi, `kruti-dev` → Hindi. Add `--source-lang` CLI option for manual override.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — add `--source-lang` option, auto-detect from encoding
- `src/legacylipi/mappings/loader.py` — ensure `MappingTable.language` is populated
- `src/legacylipi/ui/app.py` — add source language display/override in UI

---

### 4. Wire Up Bilingual Output

**Description**: The `generate_bilingual()` method already exists in `output_generator.py` (lines 269-321) and produces side-by-side original + translated Markdown tables. However, it's not wired into the CLI or web UI. Adding a `--bilingual` flag is trivial since the implementation is already done.

**Why**: Bilingual output is extremely valuable for verification, legal documents, and language learning. The feature is 80% implemented — just needs UI/CLI wiring.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — add `--bilingual` flag to `translate` command
- `src/legacylipi/ui/app.py` — add bilingual checkbox in translation settings
- `src/legacylipi/core/output_generator.py` — already implemented

---

### 5. Bundle a Devanagari Font

**Description**: Output PDFs use whatever system font is found first (`_get_unicode_font()` in `output_generator.py`, lines 1167-1200). If no Devanagari font is available (e.g., a fresh Ubuntu server or Docker container), it falls back to Helvetica which cannot render Devanagari at all — producing completely unreadable output.

**Why**: On systems without Indian fonts installed, the primary output (PDF) is broken. This is a silent failure.

**Fix**: Bundle Noto Sans Devanagari (SIL Open Font License) with the package, or download it on first use to `~/.legacylipi/fonts/`.

**Complexity**: Low

**Files**:
- `src/legacylipi/core/output_generator.py` — update font search to include bundled font
- `pyproject.toml` — include font file in package data
- Add font file to `src/legacylipi/data/fonts/`

---

### 6. Docker Image

**Description**: Create a Dockerfile that bundles Python, Tesseract with Indian language packs (`tesseract-ocr-mar`, `tesseract-ocr-hin`, etc.), and all dependencies. Expose the web UI on port 8080.

**Why**: Installing Tesseract and its language packs is the #1 barrier to adoption. A Docker image eliminates this entirely and enables server deployment for organizations.

**Complexity**: Low

**Files**:
- `Dockerfile` — new file
- `docker-compose.yml` — optional, for local development
- `.dockerignore` — exclude unnecessary files
- `README.md` — add Docker usage section

---

### 7. Split Optional Dependencies

**Description**: The current `pyproject.toml` (lines 25-37) puts `nicegui`, `pytesseract`, and `pillow` in required dependencies. Users who only want the CLI or library need NiceGUI. Users who only want font-based extraction need pytesseract.

**Why**: Smaller install footprint, faster installs, fewer dependency conflicts.

**Fix**: Move to optional dependency groups:
- `pip install legacylipi` — core library + CLI only
- `pip install legacylipi[ui]` — adds NiceGUI
- `pip install legacylipi[ocr]` — adds pytesseract + Pillow
- `pip install legacylipi[all]` — everything

**Complexity**: Low

**Files**:
- `pyproject.toml` — restructure dependencies into optional groups

---

### 8. Post-Processing Pipeline for All Encodings

**Description**: Only `shree-dev` has post-processing (`apply_shree_dev_post_processing` in `mappings/shree_dev.py`). Other Devanagari encodings need similar matra reordering, halant cleanup, and Unicode normalization. The converter (`unicode_converter.py`, line 218) only triggers post-processing for `shree-dev`.

**Why**: Raw character-by-character mapping without post-processing produces incorrect Devanagari ordering (e.g., pre-base matras in wrong position, missing virama combinations).

**Fix**: Create a pluggable post-processing system where each encoding can register its own rules. At minimum, apply Devanagari matra reordering as a generic step for all encodings.

**Complexity**: Medium

**Files**:
- `src/legacylipi/core/unicode_converter.py` — make post-processing pluggable
- `src/legacylipi/mappings/shree_dev.py` — already has post-processing (model for others)
- New post-processing functions per encoding

---

### 9. Improve Encoding Detection with Statistical Analysis

**Description**: The heuristic detection in `detect_from_text_heuristic()` (`encoding_detector.py`, lines 243-317) uses simple substring matching with small signature sets (e.g., only 10 signatures for shree-dev). This can produce false positives between similar encodings (e.g., `shree-lipi` and `dvb-tt` share some signatures like `"Ö"`).

**Why**: Incorrect encoding detection leads to garbled Unicode output with no obvious error — the worst user experience.

**Fix**: Implement character frequency distribution analysis. Build n-gram frequency profiles for each encoding from known-good documents and compare against the input text using a statistical distance metric (e.g., chi-squared or cosine similarity).

**Complexity**: Medium

**Files**:
- `src/legacylipi/core/encoding_detector.py` — add statistical detection method
- `src/legacylipi/mappings/` — add frequency profile data per encoding

---

### 10. Mapping Validation Test Framework

**Description**: No systematic round-trip testing with real document samples exists. `test_mappings.py` and `test_unicode_converter.py` test the machinery but not the quality of the actual character mappings against known-good outputs.

**Why**: Encoding mappings are the most error-prone part of the system. Without validation against known-good data, regressions can silently degrade output quality.

**Fix**: Add a test harness that takes known input/output pairs for each encoding and verifies: detection → conversion → expected Unicode output. Include at least 3 sample texts per encoding.

**Complexity**: Low

**Files**:
- `tests/test_mapping_validation.py` — new test file
- `tests/data/` — add known-good sample pairs per encoding
- `tests/conftest.py` — add fixtures for sample data

---

## Nice-to-Have Improvements

High-impact improvements that enhance the user experience and developer workflow.

---

### 11. Batch Processing / Directory Mode

**Description**: The CLI only processes one file at a time. Add a `legacylipi translate-batch <directory>` command that processes all PDFs in a folder with progress reporting and a summary table.

**Why**: Users often have dozens or hundreds of legacy PDFs to convert (e.g., an entire office archive or government department).

**Complexity**: Low (pipeline is already file-by-file internally)

**Files**:
- `src/legacylipi/cli.py` — add `translate-batch` command
- Reuse existing `translate` command logic in a loop

---

### 12. Preview / Inspect Mode

**Description**: Add a `legacylipi preview <file.pdf>` command that shows the first N lines of extracted text alongside the Unicode conversion, so users can verify encoding detection and conversion quality before committing to translation (which is slow and may cost money).

**Why**: Users currently must run the full pipeline to check if the encoding was detected correctly. A preview saves time and builds confidence.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — add `preview` command
- Reuse `pdf_parser`, `encoding_detector`, `unicode_converter`

---

### 13. Translation Caching Layer

**Description**: No translation caching exists. Re-running the same document re-translates everything, wasting time and API calls. Add a content-hash-based cache in `~/.legacylipi/cache/` that maps `(source_text_hash, source_lang, target_lang, backend)` to translation results.

**Why**: Saves time (minutes per document) and API costs during iterative workflows. Enables resumption after partial failures.

**Complexity**: Low

**Files**:
- `src/legacylipi/core/translator.py` — add cache layer around `translate_async()`
- New cache module in `src/legacylipi/core/utils/cache.py`

---

### 14. Mapping Contribution Tooling

**Description**: Add `legacylipi mapping create <encoding-name>` that scaffolds a new YAML mapping file in the correct format, and `legacylipi mapping test <encoding-name> <sample.pdf>` that applies the mapping interactively. The loader already supports YAML/JSON from external directories (`loader.py`, lines 130-142).

**Why**: The biggest bottleneck to growth is adding new encodings. Making this contributor-friendly enables community contributions.

**Complexity**: Medium

**Files**:
- `src/legacylipi/cli.py` — add `mapping` command group
- `src/legacylipi/mappings/loader.py` — scaffold template generation

---

### 15. Parallel Page Processing for OCR

**Description**: PDF parsing and OCR run sequentially page-by-page. Use `concurrent.futures.ProcessPoolExecutor` to process multiple pages simultaneously, especially for OCR which is CPU-bound and independent per page.

**Why**: OCR at 300 DPI on a 20-page document is very slow. Parallelizing across CPU cores could give a 4-8x speedup.

**Complexity**: Medium

**Files**:
- `src/legacylipi/core/ocr_parser.py` — parallelize `parse()` method across pages
- `src/legacylipi/core/pdf_parser.py` — same for font-based parsing

---

### 16. Plugin Architecture for Encodings

**Description**: Currently, adding a new encoding requires modifying 3 files: `loader.py` (add to `BUILTIN_MAPPINGS`), a new `*.py` in `mappings/`, and `encoding_detector.py` (add patterns). Instead, create a registration-based system where a single file registers everything: patterns, mappings, post-processing, and metadata.

**Why**: Reduces the number of files to modify from 3 to 1 when adding an encoding. Makes community contributions much easier.

**Complexity**: Medium

**Files**:
- `src/legacylipi/mappings/loader.py` — refactor to registration-based
- `src/legacylipi/core/encoding_detector.py` — load patterns from mapping registry

---

### 17. Interactive Encoding Override in Web UI

**Description**: When encoding detection confidence is below 80%, show a warning with a dropdown of alternative encodings and a sample of converted text for each, letting the user pick the correct one.

**Why**: The current system silently uses the best guess, which may be wrong. Users with domain knowledge should be able to override easily.

**Complexity**: Medium

**Files**:
- `src/legacylipi/ui/app.py` (or new React frontend) — add encoding override UI
- `src/legacylipi/core/encoding_detector.py` — expose alternative detections

---

### 18. CLI Progress Bar with ETA

**Description**: The CLI uses a single rich spinner with text updates but no percentage progress or ETA. For multi-page documents, add a proper progress bar with `page X/N` reporting during parsing, conversion, and translation phases.

**Why**: A 50-page document takes many minutes. Users need to know if it's stuck or progressing.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — replace spinner with `rich.progress.Progress` bar

---

### 19. Cloud-Hosted Demo Instance

**Description**: Deploy the web UI to a free-tier cloud service (Render, Railway, or Google Cloud Run) so users can try LegacyLipi without installing anything.

**Why**: Dramatically lowers the barrier to trying the tool. A demo link in the README drives adoption.

**Complexity**: Low

**Files**:
- `Dockerfile` (from item #6) — prerequisite
- `README.md` — add demo link
- Cloud platform config (e.g., `render.yaml`)

---

### 20. Backend-Aware Chunk Sizing

**Description**: `_chunk_text()` in `translator.py` (lines 1149-1200) uses a fixed 2000-character chunk size. This is conservative for OpenAI (handles 16K+) and too large for MyMemory (500 char limit, handled separately). Make chunk size backend-aware.

**Why**: Fewer chunks = fewer API calls = faster translation and fewer rate limit issues. More chunks for backends with small limits = fewer failures.

**Complexity**: Low

**Files**:
- `src/legacylipi/core/translator.py` — add `max_chunk_size` property to each backend

---

## Future Consideration

Lower-priority items for long-term roadmap.

---

### 21. Streaming Translation for Large Documents

**Description**: The current approach loads the entire document into memory, converts all text, then translates all at once. For very large documents (100+ pages), implement streaming: parse page, convert, translate, output, then move to the next page.

**Why**: Government archives can have 200+ page PDFs. Current approach will consume significant memory.

**Complexity**: High

**Files**:
- All pipeline files would need streaming interfaces

---

### 22. Paragraph-Level Translation Cache

**Description**: Beyond file-level caching (item #13), cache at the paragraph level. Many government documents share boilerplate text (headers, footers, standard paragraphs). Paragraph-level cache makes repeated content instant.

**Why**: Dramatic speed improvement for batch processing of similar documents.

**Complexity**: Medium

**Files**:
- `src/legacylipi/core/translator.py` — paragraph-level cache with content hashing

---

### 23. Document History / Session Management

**Description**: Maintain a processing log in `~/.legacylipi/history.json` tracking every processed document: input path, encoding detected, output path, timestamp, success/failure. Add `legacylipi history` and `legacylipi redo <id>` commands.

**Why**: Users processing many files need to track what they've done and retry failures.

**Complexity**: Low

**Files**:
- `src/legacylipi/cli.py` — add `history` and `redo` commands
- New module `src/legacylipi/core/utils/history.py`

---

### 24. Bundled Executable (PyInstaller)

**Description**: Create a single-file executable for Windows/macOS/Linux that includes Python and all dependencies. Users download one file and run it.

**Why**: Non-technical users (archivists, librarians, government clerks) cannot install Python or manage dependencies.

**Complexity**: High

**Files**:
- `legacylipi.spec` — PyInstaller spec file
- CI workflow for building executables

---

### 25. API Documentation Generation

**Description**: The code has excellent docstrings throughout but no generated API documentation. Set up Sphinx or MkDocs with autodoc to publish browsable API docs.

**Why**: Contributors need API reference docs. Users writing scripts against the library need documentation.

**Complexity**: Low

**Files**:
- `docs/conf.py` or `mkdocs.yml` — documentation config
- CI workflow for doc generation

---

### 26. Error Recovery with Partial Results

**Description**: If translation fails mid-document (e.g., rate limiting at page 4 of 10), the entire operation fails. Implement partial result saving: output successfully translated pages and mark failed pages as `"[Translation failed — original Unicode text follows]"`.

**Why**: Partial results are vastly better than no results, especially for large documents with expensive translations.

**Complexity**: Medium

**Files**:
- `src/legacylipi/core/translator.py` — handle partial translation results
- `src/legacylipi/core/output_generator.py` — render partial results with failure markers
- `src/legacylipi/cli.py` — display partial success warnings

---

## Summary

| Priority | Count | Complexity Breakdown |
|---|---|---|
| **Must-Have** | 10 | 5 Low, 4 Medium, 1 Low-Medium |
| **Nice-to-Have** | 10 | 5 Low, 5 Medium |
| **Future** | 6 | 2 Low, 2 Medium, 2 High |

### Recommended Implementation Order

1. **Source language auto-detection** (#3) — Low effort, high impact on translation quality
2. **Wire up bilingual output** (#4) — Already 80% implemented
3. **Fix page marker corruption** (#2) — Low effort, eliminates common failure
4. **Bundle Devanagari font** (#5) — Low effort, fixes silent PDF failures
5. **Split optional dependencies** (#7) — Low effort, better install experience
6. **Mapping validation test framework** (#10) — Foundation for all encoding work
7. **Complete missing encoding mappings** (#1) — Core value proposition
8. **Post-processing pipeline** (#8) — Required for quality encoding output
9. **Improve encoding detection** (#9) — Quality improvement
10. **Docker image** (#6) — Deployment enabler
