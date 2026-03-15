"""Tests for ai_pdf_translator.openai_client singleton."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import ai_pdf_translator.openai_client as client_mod


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the module-level singleton before each test."""
    original = client_mod._CLIENT
    client_mod._CLIENT = None
    yield
    client_mod._CLIENT = original


class TestGetClient:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            client_mod.get_client()

    def test_returns_client_instance(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        mock_client = MagicMock()
        with patch.object(client_mod, "OpenAI", return_value=mock_client):
            result = client_mod.get_client()
        assert result is mock_client

    def test_singleton_returns_same_instance(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        mock_client = MagicMock()
        with patch.object(client_mod, "OpenAI", return_value=mock_client) as mock_cls:
            first = client_mod.get_client()
            second = client_mod.get_client()
        assert first is second
        mock_cls.assert_called_once()
