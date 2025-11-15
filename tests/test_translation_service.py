from pathlib import Path

import pytest
from fpdf import FPDF

from ai_pdf_translator import translation_service


def _make_pdf(path: Path, text: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    width = pdf.w - 2 * pdf.l_margin
    for line in text.splitlines():
        pdf.multi_cell(width, 10, line or " ")
    pdf.output(str(path))


def test_translate_pdf_returns_combined_text_and_pdf(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf(pdf_path, "Hello world\nThis is a test")

    def fake_translate_chunk(chunk: str, **_: str) -> str:
        return f"translated::{chunk[:5]}"

    monkeypatch.setattr(translation_service, "translate_chunk", fake_translate_chunk)

    text, pdf_output = translation_service.translate_pdf(
        str(pdf_path),
        "English",
        "Spanish",
        progress=lambda *args, **kwargs: None,
    )

    assert "translated" in text
    assert pdf_output is not None
    assert Path(pdf_output).exists()

    Path(pdf_output).unlink()
