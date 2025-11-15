"""Integration tests that exercise the real OpenAI API."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fpdf import FPDF

from ai_pdf_translator import translation_service


pytestmark = pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY") and os.getenv("RUN_OPENAI_TESTS")),
    reason="Integration tests require OPENAI_API_KEY and RUN_OPENAI_TESTS=1",
)


def _make_pdf(path: Path, text: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    width = pdf.w - 2 * pdf.l_margin
    for line in text.splitlines():
        pdf.multi_cell(width, 10, line or " ")
    pdf.output(str(path))


@pytest.mark.integration
def test_translate_chunk_real_openai():
    result = translation_service.translate_chunk(
        "Hello world",
        source_lang="English",
        target_lang="Spanish",
    )

    assert result
    assert result.strip().lower() != "hello world"
    assert "hola" in result.lower() or "mundo" in result.lower()


@pytest.mark.integration
def test_translate_pdf_real_openai(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf(pdf_path, "Hello world.\nThis is a test.")

    text, pdf_output = translation_service.translate_pdf(
        str(pdf_path),
        "English",
        "Spanish",
        progress=lambda *args, **kwargs: None,
    )

    assert "hola" in text.lower() or "mundo" in text.lower()
    assert pdf_output is not None
    assert Path(pdf_output).exists()

    Path(pdf_output).unlink()
