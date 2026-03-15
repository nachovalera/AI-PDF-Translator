"""Tests for ai_pdf_translator.pdf_utils module."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from ai_pdf_translator.pdf_utils import (
    chunk_text,
    extract_text_from_pdf,
    text_to_pdf,
    _slugify,
    _ensure_font_file,
    _prepare_paragraphs,
)


# ── extract_text_from_pdf ──────────────────────────────────────────


class TestExtractTextFromPdf:
    def test_from_string_path(self, sample_pdf):
        text = extract_text_from_pdf(str(sample_pdf))
        assert "Hello world" in text

    def test_from_path_object(self, sample_pdf):
        text = extract_text_from_pdf(sample_pdf)  # Path object
        assert "Hello world" in text

    def test_from_bytes(self, sample_pdf):
        raw = BytesIO(sample_pdf.read_bytes())
        text = extract_text_from_pdf(raw)
        assert "Hello world" in text

    def test_empty_pdf(self, tmp_path):
        """A PDF with a blank page should return empty/whitespace-only text."""
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()  # blank page, no text
        path = tmp_path / "empty.pdf"
        pdf.output(str(path))

        text = extract_text_from_pdf(str(path))
        assert text.strip() == ""

    def test_corrupt_bytes_raises(self):
        with pytest.raises(Exception):
            extract_text_from_pdf(b"this is not a PDF")

    def test_multi_page_pdf(self, tmp_path):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_font("Helvetica", size=12)
        for i in range(3):
            pdf.add_page()
            pdf.cell(text=f"Page {i + 1}")
        path = tmp_path / "multi.pdf"
        pdf.output(str(path))

        text = extract_text_from_pdf(str(path))
        assert "Page 1" in text
        assert "Page 3" in text


# ── chunk_text ─────────────────────────────────────────────────────


class TestChunkText:
    def test_respects_max_chars(self):
        paragraph = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        text = "\n".join([paragraph] * 10)
        chunks = chunk_text(text, max_chars=120)
        assert len(chunks) > 1
        assert all(len(chunk) <= 150 for chunk in chunks)

    def test_empty_string(self):
        result = chunk_text("")
        assert result == [""]

    def test_single_paragraph_over_limit(self):
        big = "A" * 500
        chunks = chunk_text(big, max_chars=100)
        assert len(chunks) >= 5
        assert all(len(c) <= 100 for c in chunks)

    def test_whitespace_only(self):
        result = chunk_text("   \n  \n   ")
        # No non-empty paragraphs found, so returns [cleaned] as fallback
        assert len(result) == 1
        assert result[0].strip() == ""

    def test_no_paragraph_breaks(self):
        text = "Line one\nLine two\nLine three"
        chunks = chunk_text(text, max_chars=5000)
        joined = "\n\n".join(chunks)
        assert "Line one" in joined
        assert "Line three" in joined

    def test_preserves_all_content(self):
        paragraphs = [f"Paragraph number {i}" for i in range(20)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, max_chars=100)
        combined = "\n\n".join(chunks)
        for p in paragraphs:
            assert p in combined

    def test_carriage_return_cleaned(self):
        text = "Hello\r\nworld"
        chunks = chunk_text(text, max_chars=5000)
        for chunk in chunks:
            assert "\r" not in chunk


# ── _slugify ───────────────────────────────────────────────────────


class TestSlugify:
    def test_normal_name(self):
        assert _slugify("my-file") == "my-file"

    def test_special_chars(self):
        result = _slugify("hello world!@#.pdf")
        assert "!" not in result
        assert "@" not in result
        assert " " not in result

    def test_empty_string(self):
        assert _slugify("") == "translation"

    def test_only_special_chars(self):
        assert _slugify("!!!") == "translation"

    def test_unicode_chars(self):
        result = _slugify("café_résumé")
        assert result  # non-empty
        assert isinstance(result, str)


# ── _ensure_font_file ─────────────────────────────────────────────


class TestEnsureFontFile:
    def test_raises_when_font_missing(self, monkeypatch):
        monkeypatch.setattr(
            "ai_pdf_translator.pdf_utils.FONT_PATH",
            Path("/nonexistent/font.ttf"),
        )
        with pytest.raises(RuntimeError, match="Missing fonts"):
            _ensure_font_file()

    def test_passes_when_font_exists(self):
        _ensure_font_file()  # should not raise if font is present


# ── _prepare_paragraphs ───────────────────────────────────────────


class TestPrepareParagraphs:
    def test_normal_text(self):
        result = _prepare_paragraphs("Hello\n\nWorld")
        assert result == ["Hello", "World"]

    def test_empty_text(self):
        result = _prepare_paragraphs("")
        assert result == ["No translated content available."]

    def test_whitespace_only(self):
        result = _prepare_paragraphs("   \n\n   ")
        assert result == ["No translated content available."]

    def test_strips_zero_width_chars(self):
        text = "Hello\u200BWorld\n\nFoo\uFEFFBar"
        result = _prepare_paragraphs(text)
        assert result == ["HelloWorld", "FooBar"]

    def test_normalises_carriage_returns(self):
        text = "Paragraph one\r\n\r\nParagraph two"
        result = _prepare_paragraphs(text)
        assert result == ["Paragraph one", "Paragraph two"]


# ── text_to_pdf ────────────────────────────────────────────────────


class TestTextToPdf:
    def test_creates_pdf_file(self):
        output_path = text_to_pdf(
            "Hola mundo\n\nEsto es una prueba",
            original_name="demo.pdf",
            source_lang="English",
            target_lang="Spanish",
        )
        pdf_file = Path(output_path)
        assert pdf_file.exists()
        reader = PdfReader(str(pdf_file))
        assert len(reader.pages) >= 1
        pdf_file.unlink()

    def test_without_original_name(self):
        output_path = text_to_pdf(
            "Translated text here",
            source_lang="English",
            target_lang="French",
        )
        pdf_file = Path(output_path)
        assert pdf_file.exists()
        assert "translation" in pdf_file.name
        pdf_file.unlink()

    def test_empty_text_produces_fallback(self):
        output_path = text_to_pdf(
            "",
            original_name="empty.pdf",
            source_lang="English",
            target_lang="German",
        )
        pdf_file = Path(output_path)
        assert pdf_file.exists()
        reader = PdfReader(str(pdf_file))
        page_text = reader.pages[0].extract_text() or ""
        assert "No translated content available" in page_text
        pdf_file.unlink()

    def test_special_chars_in_original_name(self):
        output_path = text_to_pdf(
            "Some content",
            original_name="my file (draft) [v2].pdf",
            source_lang="English",
            target_lang="Italian",
        )
        pdf_file = Path(output_path)
        assert pdf_file.exists()
        pdf_file.unlink()

    def test_filename_contains_language_codes(self):
        output_path = text_to_pdf(
            "Content",
            original_name="report.pdf",
            source_lang="English",
            target_lang="Spanish",
        )
        pdf_file = Path(output_path)
        assert "en_to_sp" in pdf_file.name
        pdf_file.unlink()
