"""Tests for ai_pdf_translator.translation_service module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError

from ai_pdf_translator import translation_service


# ── helpers ────────────────────────────────────────────────────────


def _noop_progress(*_args, **_kwargs):
    """Stub progress callback for tests."""


def _make_mock_response(content: str | None = "translated text"):
    """Build a fake OpenAI ChatCompletion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ── translate_chunk ────────────────────────────────────────────────


class TestTranslateChunk:
    def test_returns_translated_text(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("Hola mundo")
        monkeypatch.setattr(translation_service, "get_client", lambda: mock_client)

        result = translation_service.translate_chunk(
            "Hello world", source_lang="English", target_lang="Spanish"
        )
        assert result == "Hola mundo"

    def test_handles_none_content(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(None)
        monkeypatch.setattr(translation_service, "get_client", lambda: mock_client)

        result = translation_service.translate_chunk(
            "Hello", source_lang="English", target_lang="French"
        )
        assert result == ""

    def test_passes_model_parameter(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")
        monkeypatch.setattr(translation_service, "get_client", lambda: mock_client)

        translation_service.translate_chunk(
            "Hi", source_lang="English", target_lang="German", model="gpt-4o"
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"

    def test_system_prompt_contains_languages(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")
        monkeypatch.setattr(translation_service, "get_client", lambda: mock_client)

        translation_service.translate_chunk(
            "Bonjour", source_lang="French", target_lang="Portuguese"
        )

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        assert "French" in system_msg
        assert "Portuguese" in system_msg


# ── translate_pdf ──────────────────────────────────────────────────


class TestTranslatePdf:
    def test_returns_combined_text_and_pdf(self, monkeypatch, sample_pdf):
        def fake_translate_chunk(chunk: str, **_):
            return f"translated::{chunk[:5]}"

        monkeypatch.setattr(translation_service, "translate_chunk", fake_translate_chunk)

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

    def test_openai_error_returns_error_message(self, monkeypatch, sample_pdf):
        def failing_translate(chunk: str, **_):
            raise OpenAIError("Rate limit exceeded")

        monkeypatch.setattr(translation_service, "translate_chunk", failing_translate)

        text, pdf_path = translation_service.translate_pdf(
            str(sample_pdf), "English", "Spanish", progress=_noop_progress,
        )
        assert "failed" in text.lower()
        assert "chunk" in text.lower()
        assert pdf_path is None

    def test_gradio_file_object(self, monkeypatch, sample_pdf):
        """Simulate a Gradio-uploaded file object with a .name attribute."""
        file_obj = MagicMock()
        file_obj.name = str(sample_pdf)

        def fake_translate_chunk(chunk: str, **_):
            return "translated"

        monkeypatch.setattr(translation_service, "translate_chunk", fake_translate_chunk)

        text, pdf_path = translation_service.translate_pdf(
            file_obj, "English", "Spanish", progress=_noop_progress,
        )
        assert pdf_path is not None
        assert Path(pdf_path).exists()
        Path(pdf_path).unlink()

    def test_progress_callback_called(self, monkeypatch, sample_pdf):
        calls: list[tuple] = []

        def tracking_progress(*args, **kwargs):
            calls.append((args, kwargs))

        def fake_translate_chunk(chunk: str, **_):
            return "done"

        monkeypatch.setattr(translation_service, "translate_chunk", fake_translate_chunk)

        text, pdf_path = translation_service.translate_pdf(
            str(sample_pdf), "English", "Spanish", progress=tracking_progress,
        )
        assert len(calls) >= 2  # at least: "Reading PDF" + "Completed"
        Path(pdf_path).unlink()

    def test_multiple_chunks_all_translated(self, monkeypatch, tmp_path):
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

        def counting_translate(chunk: str, **_):
            nonlocal chunk_count
            chunk_count += 1
            return f"[translated chunk {chunk_count}]"

        monkeypatch.setattr(translation_service, "translate_chunk", counting_translate)

        text, pdf_path = translation_service.translate_pdf(
            str(path), "English", "Spanish", progress=_noop_progress,
        )
        assert chunk_count >= 1
        assert pdf_path is not None
        Path(pdf_path).unlink()
