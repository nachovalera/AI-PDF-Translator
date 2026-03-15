"""Translation orchestration using provider abstraction and PDF helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import gradio as gr

from .provider import TranslationError, TranslationProvider, get_provider
from .pdf_utils import chunk_text, extract_text_from_pdf, text_to_pdf
from .settings import DEFAULT_MODEL


_provider: TranslationProvider | None = None


def _get_provider() -> TranslationProvider:
    """Return the module-level provider, lazily initialised."""
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider


def set_provider(provider: TranslationProvider | None) -> None:
    """Override the module-level provider. Pass None to reset to default."""
    global _provider
    _provider = provider


def translate_chunk(
    chunk: str,
    *,
    source_lang: str,
    target_lang: str,
    model: str | None = None,
) -> str:
    provider = _get_provider()
    resolved_model = model if model is not None else getattr(provider, "default_model", DEFAULT_MODEL)
    return provider.translate(
        chunk,
        source_lang=source_lang,
        target_lang=target_lang,
        model=resolved_model,
    )


def translate_pdf(
    pdf_file,
    source_language: str,
    target_language: str,
    progress=gr.Progress(track_tqdm=True),
) -> Tuple[str, str | None]:
    if pdf_file is None:
        return "Please upload a PDF to translate.", None

    progress(0.02, desc="Reading PDF…")
    pdf_path = getattr(pdf_file, "name", None) or pdf_file
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        return "No extractable text found in the PDF.", None

    chunks = chunk_text(text)
    translated_chunks: list[str] = []
    total = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):
        progress(
            0.05 + (idx - 1) / max(total, 1) * 0.9,
            desc=f"Translating chunk {idx}/{total}",
        )
        try:
            translated = translate_chunk(
                chunk,
                source_lang=source_language,
                target_lang=target_language,
            )
        except TranslationError as exc:
            return f"Translation failed on chunk {idx}/{total}: {exc}", None

        translated_chunks.append(translated)

    translated_text = "\n\n".join(translated_chunks)
    pdf_download_path = text_to_pdf(
        translated_text,
        original_name=Path(pdf_path).name if isinstance(pdf_path, (str, Path)) else None,
        source_lang=source_language,
        target_lang=target_language,
    )

    progress(1.0, desc="Completed")
    return translated_text, pdf_download_path


__all__ = ["translate_chunk", "translate_pdf", "set_provider"]
