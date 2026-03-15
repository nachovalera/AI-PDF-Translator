# AI-PDF-Translator Roadmap

Track the status of planned features and improvements. Update this file as items are implemented.

**Legend:** ⬜ Planned · 🔄 In Progress · ✅ Done

---

## Architecture & Refactoring

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 1 | Abstract AI provider interface (`TranslationProvider` protocol/ABC) | ✅ Done | `provider.py`: `TranslationProvider` protocol, `OpenAIProvider`, `TranslationError`, `get_provider()` factory; `translation_service.py` decoupled from OpenAI SDK |
| 2 | Anthropic Claude as alternative translation provider | ✅ Done | `AnthropicProvider` in `provider.py`; `anthropic_client.py` singleton; `get_provider("anthropic")` factory; set `TRANSLATION_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` to use |
| 3 | Multi-provider comparison mode | ⬜ Planned | Translate same PDF with 2+ providers simultaneously; show results side-by-side in UI |
| 4 | Third-party PDF translation service integration (e.g. DeepL Document API) | ⬜ Planned | Research + implement services that accept full PDFs and return translated PDFs |

---

## Testing / TDD

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 5 | Expand test suite with TDD approach | ✅ Done | Added 45 unit tests covering settings, openai_client singleton, pdf_utils (extract, chunk, slugify, font, paragraphs, pdf gen), translation_service (translate_chunk mock, error paths, progress, Gradio file objects) |
| 6 | Contract tests for provider abstraction layer | ✅ Done | `TestProviderContract` in `test_provider.py` — parameterized over OpenAI and Anthropic providers; verifies protocol compliance, return types, error wrapping, and `default_model` attribute |

---

## Core Features

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 7 | Auto-detect source language | ⬜ Planned | Use LLM or `langdetect` to infer language; remove requirement to manually select source |
| 8 | Layout preservation in translated PDF | ⬜ Planned | Replace plain text extraction with `pdfplumber`/`pymupdf` to preserve columns, headers, tables |
| 9 | Handle images/figures containing text | ⬜ Planned | Use vision-capable model (GPT-4o / Claude) to OCR and translate embedded image text |
| 10 | Streaming translation progress | ⬜ Planned | Stream token output per chunk so UI updates in real time |
| 11 | Translation caching to reduce API costs | ⬜ Planned | Cache chunk translations by content hash (in-memory or SQLite); avoid re-translating identical paragraphs |
| 12 | Retry logic with exponential backoff | ⬜ Planned | Wrap `translate_chunk` calls with retry (e.g. `tenacity`) for API failures |

---

## UX Improvements

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 13 | Multi-file batch upload | ⬜ Planned | Accept multiple PDFs in one session, translate sequentially |
| 14 | Side-by-side original/translated preview | ⬜ Planned | Show extracted source text and translated text in UI before PDF download |
| 15 | Model/provider selection dropdown in UI | ⬜ Planned | Expose `OPENAI_TRANSLATION_MODEL` and provider choice as Gradio dropdowns |
| 16 | Cost estimation before translating | ⬜ Planned | Estimate token count and approximate API cost before starting |
| 17 | Custom glossary / terminology enforcement | ⬜ Planned | Let users supply key-value term pairs injected into the system prompt |

---

## Deployment

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 18 | Dockerfile for self-hosting | ⬜ Planned | Multi-stage Docker build, expose port 7860 |
| 19 | REST API endpoint alongside Gradio UI | ⬜ Planned | FastAPI route `POST /translate` accepting PDF bytes, returning translated PDF |
| 20 | Expand supported languages | ⬜ Planned | Add Japanese, Chinese, Arabic, Hindi, etc. to `LANGUAGES` list in `interface.py` |

---

## Completed

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 1 | Abstract AI provider interface (`TranslationProvider` protocol/ABC) | ✅ Done | `provider.py`: protocol, `OpenAIProvider`, `TranslationError`, `get_provider()` factory |
| 2 | Anthropic Claude as alternative translation provider | ✅ Done | `AnthropicProvider` + `anthropic_client.py` singleton; `TRANSLATION_PROVIDER=anthropic` env var |
| 5 | Expand test suite with TDD approach | ✅ Done | 48 unit tests across 5 test files; covers settings, openai_client, pdf_utils, translation_service |
| 6 | Contract tests for provider abstraction layer | ✅ Done | Parameterized `TestProviderContract` in `test_provider.py`; covers both OpenAI and Anthropic |
