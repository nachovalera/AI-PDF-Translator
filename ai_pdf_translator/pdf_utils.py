"""PDF helpers for extraction, chunking, and export."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List
from uuid import uuid4

from fpdf import FPDF
from fpdf.errors import FPDFException
from pypdf import PdfReader

from .settings import FONT_PATH, MAX_CHARS_PER_CHUNK, PDF_OUTPUT_DIR


def extract_text_from_pdf(pdf_source: str | Path | bytes) -> str:
    """Read text from a PDF path or bytes payload."""
    if isinstance(pdf_source, (str, Path)):
        reader = PdfReader(str(pdf_source))
    else:
        reader = PdfReader(pdf_source)

    pages_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n".join(pages_text)


def chunk_text(text: str, max_chars: int | None = None) -> List[str]:
    """Split text into manageable chunks by paragraph boundaries."""
    limit = max_chars or MAX_CHARS_PER_CHUNK
    cleaned = text.replace("\r", "")
    paragraphs = [p.strip() for p in cleaned.split("\n") if p.strip()]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if current_len + len(paragraph) + 1 > limit and current:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0

        if len(paragraph) > limit:
            for start in range(0, len(paragraph), limit):
                sliced = paragraph[start : start + limit]
                if current:
                    chunks.append("\n\n".join(current))
                    current = []
                    current_len = 0
                chunks.append(sliced)
            continue

        current.append(paragraph)
        current_len += len(paragraph) + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks or [cleaned]


def _slugify(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
    sanitized = sanitized.strip("_")
    return sanitized or "translation"


_ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")


def _ensure_font_file() -> None:
    if not FONT_PATH.exists():
        raise RuntimeError(
            "Missing fonts/DejaVuSans.ttf. Please ensure the Unicode font is available."
        )


def _prepare_paragraphs(text: str) -> List[str]:
    cleaned = _ZERO_WIDTH_RE.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    if not cleaned.strip():
        return ["No translated content available."]

    sections = re.split(r"\n\s*\n", cleaned)
    paragraphs = [section.strip() for section in sections if section.strip()]
    return paragraphs or ["No translated content available."]


def text_to_pdf(
    text: str,
    *,
    original_name: str | None = None,
    source_lang: str,
    target_lang: str,
) -> str:
    """Persist translated text into a PDF file and return its path."""
    _ensure_font_file()
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base = _slugify(Path(original_name).stem) if original_name else "translation"
    suffix = f"{source_lang[:2].lower()}_to_{target_lang[:2].lower()}"
    filename = PDF_OUTPUT_DIR / f"{base}_{suffix}_{uuid4().hex[:8]}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("DejaVuSans", "", str(FONT_PATH))
    pdf.set_font("DejaVuSans", size=12)
    pdf.set_text_color(0, 0, 0)

    title = original_name or "PDF translation"
    header = f"{title} — {source_lang} → {target_lang}"
    pdf.multi_cell(0, 8, header, align="L")
    pdf.ln(4)

    for paragraph in _prepare_paragraphs(text):
        safe_text = paragraph if paragraph.strip() else " "
        try:
            pdf.multi_cell(0, 7, safe_text, align="L")
        except FPDFException:
            remaining = safe_text
            while remaining:
                pdf.multi_cell(0, 7, remaining[:1000], align="L")
                remaining = remaining[1000:]
        pdf.ln(2)

    pdf.output(str(filename))
    return str(filename)


__all__ = [
    "extract_text_from_pdf",
    "chunk_text",
    "text_to_pdf",
]
