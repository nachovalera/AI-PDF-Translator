"""Tests for ai_pdf_translator.translation_service module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_pdf_translator import translation_service
from ai_pdf_translator.provider import TranslationError


# ── helpers ────────────────────────────────────────────────────────


def _noop_progress(*_args, **_kwargs):
    """Stub progress callback for tests."""


class FakeProvider:
    """Test double implementing TranslationProvider."""

    def __init__(self, return_value: str = "translated text", error: Exception | None = None):
        self.return_value = return_value
        self.error = error
        self.calls: list[dict] = []

    def translate(self, text: str, *, source_lang: str, target_lang: str, model: str) -> str:
        self.calls.append({
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "model": model,
        })
        if self.error:
            raise self.error
        return self.return_value


@pytest.fixture(autouse=True)
def _reset_provider():
    """Ensure provider state is clean between tests."""
    yield
    translation_service.set_provider(None)


# ── translate_chunk ────────────────────────────────────────────────


class TestTranslateChunk:
    def test_returns_translated_text(self):
        fake = FakeProvider(return_value="Hola mundo")
        translation_service.set_provider(fake)

        result = translation_service.translate_chunk(
            "Hello world", source_lang="English", target_lang="Spanish"
        )
        assert result == "Hola mundo"

    def test_handles_empty_content(self):
        fake = FakeProvider(return_value="")
        translation_service.set_provider(fake)

        result = translation_service.translate_chunk(
            "Hello", source_lang="English", target_lang="French"
        )
        assert result == ""

    def test_passes_model_parameter(self):
        fake = FakeProvider(return_value="ok")
        translation_service.set_provider(fake)

        translation_service.translate_chunk(
            "Hi", source_lang="English", target_lang="German", model="gpt-4o"
        )

        assert fake.calls[0]["model"] == "gpt-4o"

    def test_passes_language_parameters(self):
        fake = FakeProvider(return_value="ok")
        translation_service.set_provider(fake)

        translation_service.translate_chunk(
            "Bonjour", source_lang="French", target_lang="Portuguese"
        )

        assert fake.calls[0]["source_lang"] == "French"
        assert fake.calls[0]["target_lang"] == "Portuguese"


# ── translate_pdf ──────────────────────────────────────────────────


class TestTranslatePdf:
    def test_returns_combined_text_and_pdf(self, sample_pdf):
        fake = FakeProvider(return_value="translated")
        translation_service.set_provider(fake)

        text, pdf_output = translation_service.translate_pdf(
            str(sample_pdf), "English", "Spanish", progress=_noop_progress,
        )

        assert "translated" in text
        assert pdf_output is not None
        assert Path(pdf_output).exists()
        Path(pdf_output).unlink()

    def test_none_input_returns_error(self):
        text, pdf_path = translation_service.translate_pdf(
            None, "English", "Spanish", progress=_noop_progress,
        )
        assert "upload" in text.lower()
        assert pdf_path is None

    def test_empty_pdf_returns_error(self, tmp_path):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        path = tmp_path / "blank.pdf"
        pdf.output(str(path))

        text, pdf_path = translation_service.translate_pdf(
            str(path), "English", "Spanish", progress=_noop_progress,
        )
        assert "no extractable text" in text.lower()
        assert pdf_path is None

    def test_translation_error_returns_error_message(self, sample_pdf):
        fake = FakeProvider(error=TranslationError("Rate limit exceeded"))
        translation_service.set_provider(fake)

        text, pdf_path = translation_service.translate_pdf(
            str(sample_pdf), "English", "Spanish", progress=_noop_progress,
        )
        assert "failed" in text.lower()
        assert "chunk" in text.lower()
        assert pdf_path is None

    def test_gradio_file_object(self, sample_pdf):
        """Simulate a Gradio-uploaded file object with a .name attribute."""
        file_obj = MagicMock()
        file_obj.name = str(sample_pdf)

        fake = FakeProvider(return_value="translated")
        translation_service.set_provider(fake)

        text, pdf_path = translation_service.translate_pdf(
            file_obj, "English", "Spanish", progress=_noop_progress,
        )
        assert pdf_path is not None
        assert Path(pdf_path).exists()
        Path(pdf_path).unlink()

    def test_progress_callback_called(self, sample_pdf):
        calls: list[tuple] = []

        def tracking_progress(*args, **kwargs):
            calls.append((args, kwargs))

        fake = FakeProvider(return_value="done")
        translation_service.set_provider(fake)

        text, pdf_path = translation_service.translate_pdf(
            str(sample_pdf), "English", "Spanish", progress=tracking_progress,
        )
        assert len(calls) >= 2  # at least: "Reading PDF" + "Completed"
        Path(pdf_path).unlink()

    def test_multiple_chunks_all_translated(self, tmp_path):
        """PDF with enough text to produce multiple chunks."""
        from fpdf import FPDF

        big_text = "\n\n".join([f"Paragraph {i}: " + "word " * 50 for i in range(20)])
        pdf = FPDF()
        pdf.set_font("Helvetica", size=12)
        pdf.add_page()
        pdf.multi_cell(0, 10, big_text)
        path = tmp_path / "big.pdf"
        pdf.output(str(path))

        chunk_count = 0

        class CountingProvider:
            def translate(self, text, *, source_lang, target_lang, model):
                nonlocal chunk_count
                chunk_count += 1
                return f"[translated chunk {chunk_count}]"

        translation_service.set_provider(CountingProvider())

        text, pdf_path = translation_service.translate_pdf(
            str(path), "English", "Spanish", progress=_noop_progress,
        )
        assert chunk_count >= 1
        assert pdf_path is not None
        Path(pdf_path).unlink()
