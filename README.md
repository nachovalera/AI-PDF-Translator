# AI PDF Translator

Translate long PDFs between languages using OpenAI and a friendly Gradio UI. By default the app translates English → Spanish, but you can switch to any supported pair in the interface.

## Features
- Extracts text from PDFs of arbitrary length using `pypdf`
- Splits content into configurable chunks so 100+ page documents can be processed safely
- Uses the OpenAI Responses API for high-quality translations while preserving structure
- Provides a browser-based Gradio interface for uploading PDFs, reading the translated output, and downloading it as a fresh PDF whose filename mirrors the original with a `{src}_to_{dst}` suffix

## Requirements
- Python 3.10+
- OpenAI API key with access to GPT-5-mini (or another translation-capable model)
- `fonts/DejaVuSans.ttf` is included for Unicode-safe PDF exports (sourced from the [DejaVu fonts project](https://dejavu-fonts.github.io/))
- Generated PDFs are stored locally under `translated_pdfs/` (ignored by git) using the original filename plus the language suffix

## Setup
1. (Optional) Create and activate a virtual environment.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```
3. Provide your OpenAI API key.
   ```bash
   cp .env.example .env
   # edit .env and set OPENAI_API_KEY
   ```

## Running the app
```bash
python app.py
```
Gradio starts a local server and prints URLs in the terminal. Open the `http://127.0.0.1:7860` link, upload a PDF, choose source/target languages, and click **Translate PDF**. The translated text appears in the textbox, and a **Download translated PDF** button lets you grab a PDF version of the translation.

## Configuration
Environment variables (set them in `.env` or your shell):

| Name | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | Required OpenAI credential | — |
| `OPENAI_TRANSLATION_MODEL` | Model used for translation | `gpt-5-mini` |
| `MAX_CHARS_PER_CHUNK` | Character limit for each translation chunk | `3500` |

Lowering `MAX_CHARS_PER_CHUNK` trades throughput for higher reliability on very large files.

## Testing
Run the automated test suite (also executed in CircleCI) with:
```bash
pytest
```
Integration tests hit the real OpenAI API; they run only when both `OPENAI_API_KEY` and `RUN_OPENAI_TESTS=1` are set (CircleCI sets both via project settings). Locally you can omit `RUN_OPENAI_TESTS` to skip them.

## Notes & next steps
- Add support for more advanced formatting (tables, images) in the generated PDF if needed.
- Extend the language list or add automatic language detection.

## Contributing
Issues and pull requests are welcome. Please run `pytest` (and set `RUN_OPENAI_TESTS=1` if you want to include integration tests) before opening a PR.

## License
Released under the [MIT License](LICENSE).
