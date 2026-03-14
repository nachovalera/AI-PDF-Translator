# CLAUDE.md — AI-PDF-Translator

This file provides guidance for AI assistants (Claude, Copilot, etc.) working in this repository.

---

## Project Overview

AI-PDF-Translator is a Python application that translates PDF documents between languages using the OpenAI Chat Completions API. It exposes a Gradio web UI for file upload, language selection, and downloading translated PDFs.

---

## Repository Structure

```
AI-PDF-Translator/
├── app.py                          # Entry point — launches Gradio app
├── ai_pdf_translator/              # Core package
│   ├── __init__.py                 # Exports: build_interface, translate_pdf
│   ├── settings.py                 # Config constants & env variable loading
│   ├── openai_client.py            # Singleton OpenAI client factory
│   ├── pdf_utils.py                # PDF extraction, chunking, and generation
│   ├── translation_service.py      # Translation orchestration (main workflow)
│   └── interface.py                # Gradio UI definition
├── tests/
│   ├── conftest.py                 # Adds repo root to sys.path
│   ├── test_pdf_utils.py           # Unit tests for pdf_utils
│   ├── test_translation_service.py # Unit tests with mocked OpenAI calls
│   └── test_integration_openai.py  # Integration tests (real OpenAI API)
├── fonts/
│   └── DejaVuSans.ttf              # Unicode font for PDF output
├── .circleci/config.yml            # CI pipeline (Python 3.11)
├── .env.example                    # Environment variable template
├── pytest.ini                      # Pytest marker configuration
└── requirements.txt                # Python dependencies
```

---

## Tech Stack

| Component | Library/Tool | Version |
|-----------|-------------|---------|
| Web UI | Gradio | ≥ 4.24.0 |
| LLM API | OpenAI Python SDK | ≥ 1.14.0 |
| PDF reading | pypdf | ≥ 4.2.0 |
| PDF writing | fpdf2 | ≥ 2.7.8 |
| Env config | python-dotenv | ≥ 1.0.1 |
| Testing | pytest | ≥ 8.3.0 |
| CI/CD | CircleCI | Python 3.11 image |

---

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Then fill in OPENAI_API_KEY
python app.py                      # Opens Gradio UI at http://localhost:7860
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key (sk-...) |
| `OPENAI_TRANSLATION_MODEL` | No | `gpt-4o-mini` | Chat model to use for translation |
| `MAX_CHARS_PER_CHUNK` | No | `3500` | Max characters per translation chunk |

Variables are loaded from `.env` via `python-dotenv` in `settings.py`. The `.env` file is git-ignored — never commit it.

---

## Key Modules & Conventions

### `settings.py`
- Defines `ROOT_DIR`, `FONT_PATH`, and `PDF_OUTPUT_DIR` (the `translated_pdfs/` directory).
- `ensure_api_key()` raises `ValueError` if `OPENAI_API_KEY` is missing — called before any OpenAI usage.

### `openai_client.py`
- Implements a **singleton pattern**: `get_client()` creates the `OpenAI` instance once and reuses it.
- Do not instantiate `OpenAI()` directly elsewhere; always call `get_client()`.

### `pdf_utils.py`
- `extract_text_from_pdf(source)` — accepts a file path (str/Path) or raw bytes.
- `chunk_text(text, max_chars)` — splits on paragraph boundaries (`\n\n`), never mid-paragraph.
- `text_to_pdf(text, source_lang, target_lang)` — writes a PDF to `translated_pdfs/` using the DejaVuSans font; returns the output file path. Filenames include a UUID to avoid collisions.
- The `translated_pdfs/` output directory is git-ignored.

### `translation_service.py`
- `translate_chunk(chunk, source_lang, target_lang)` — sends a single chunk to the OpenAI Chat API with a professional translator system prompt.
- `translate_pdf(pdf_file, source_lang, target_lang, progress)` — full orchestration: extract → chunk → translate each chunk (with Gradio progress updates) → combine → write PDF. Returns `(translated_text: str, pdf_path: str)`.

### `interface.py`
- Supported languages: English, Spanish, French, German, Italian, Portuguese.
- Defaults: source = English, target = Spanish.
- The UI wires the "Translate" button directly to `translate_pdf()`.

---

## Testing

### Run unit tests (no API key needed)

```bash
pytest
```

### Run all tests including integration tests (real OpenAI calls)

```bash
RUN_OPENAI_TESTS=1 pytest
```

Integration tests in `test_integration_openai.py` are skipped unless both `OPENAI_API_KEY` and `RUN_OPENAI_TESTS=1` are set.

### Writing tests
- Unit tests mock `translate_chunk` via `monkeypatch` — do not make real API calls in unit tests.
- Use `@pytest.mark.integration` for any test that calls an external service.
- `conftest.py` adds the repo root to `sys.path`; no special import tricks are needed.

### Compile check (mirrors CI)

```bash
python -m py_compile app.py ai_pdf_translator/*.py
```

---

## CI/CD (CircleCI)

The `.circleci/config.yml` pipeline:
1. Installs dependencies from `requirements.txt`.
2. Runs `py_compile` on all Python files as a syntax check.
3. Runs the full test suite with `RUN_OPENAI_TESTS=1` using the `OpenAI-context` secret.

All tests (including integration) must pass in CI before merging.

---

## Coding Conventions

- **Python 3.10+** — use modern type hints (`list[str]` not `List[str]`).
- Follow existing module boundaries; do not add OpenAI calls outside `openai_client.py` and `translation_service.py`.
- Use `settings.py` constants (`FONT_PATH`, `PDF_OUTPUT_DIR`, etc.) instead of hardcoded paths.
- Keep the `get_client()` singleton — avoid creating multiple `OpenAI()` instances.
- Gradio progress callbacks are passed into `translate_pdf()`; update them at meaningful steps (extraction, each chunk translation).
- New languages should be added to the `LANGUAGES` list in `interface.py` only.

---

## What to Avoid

- Do not commit `.env` or any file containing API keys.
- Do not write to `translated_pdfs/` outside of `text_to_pdf()`.
- Do not bypass `ensure_api_key()` — it is the single gate for missing credentials.
- Do not add real HTTP calls to unit tests; mock external dependencies.
- Do not add new dependencies without updating `requirements.txt`.
