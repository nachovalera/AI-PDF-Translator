"""Translation orchestration using OpenAI and PDF helpers."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import gradio as gr
from openai import OpenAIError

from .openai_client import get_client
from .pdf_utils import chunk_text, extract_text_from_pdf, text_to_pdf
from .settings import DEFAULT_MODEL


def _extract_response_text(response) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    segments: List[str] = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "message":
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) == "text":
                    segments.append(content.text)

    if segments:
        return "".join(segments)

    choices = getattr(response, "choices", None)
    if choices:
        first = choices[0]
        message = getattr(first, "message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                fragment if isinstance(fragment, str) else fragment.get("text", "")
                for fragment in content
            )

    return ""


def translate_chunk(
    chunk: str,
    *,
    source_lang: str,
    target_lang: str,
    model: str = DEFAULT_MODEL,
) -> str:
    prompt = (
        "You are a professional translator. Translate the user's text from "
        f"{source_lang} to {target_lang}. Preserve the original structure, lists, "
        "headers, and quotations. Do not add commentary, only provide the translated text."
    )

    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chunk},
        ],
    )

    return response.choices[0].message.content or ""


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
    translated_chunks: List[str] = []
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
        except OpenAIError as exc:
            return f"OpenAI translation failed on chunk {idx}/{total}: {exc}", None

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


__all__ = ["translate_chunk", "translate_pdf"]
