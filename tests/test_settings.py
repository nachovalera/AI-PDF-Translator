"""Tests for ai_pdf_translator.settings module."""

from __future__ import annotations

import os

import pytest

from ai_pdf_translator.settings import ensure_api_key, MAX_CHARS_PER_CHUNK


class TestEnsureApiKey:
    def test_raises_when_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            ensure_api_key()

    def test_passes_when_key_present(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        ensure_api_key()  # should not raise

    def test_raises_when_key_is_empty_string(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            ensure_api_key()


class TestConstants:
    def test_max_chars_per_chunk_is_positive_int(self):
        assert isinstance(MAX_CHARS_PER_CHUNK, int)
        assert MAX_CHARS_PER_CHUNK > 0
