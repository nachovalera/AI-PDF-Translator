"""Tests for ai_pdf_translator.provider module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

from ai_pdf_translator.provider import (
    OpenAIProvider,
    TranslationError,
    TranslationProvider,
    _build_system_prompt,
    get_provider,
)


# ── _build_system_prompt ──────────────────────────────────────────


class TestBuildSystemPrompt:
    def test_contains_source_and_target_languages(self):
        prompt = _build_system_prompt("French", "Portuguese")
        assert "French" in prompt
        assert "Portuguese" in prompt

    def test_contains_translator_instruction(self):
        prompt = _build_system_prompt("English", "Spanish")
        assert "professional translator" in prompt.lower()


# ── TranslationProvider protocol ──────────────────────────────────


class TestTranslationProviderProtocol:
    def test_openai_provider_satisfies_protocol(self):
        provider = OpenAIProvider(client=MagicMock())
        assert isinstance(provider, TranslationProvider)

    def test_custom_class_satisfies_protocol(self):
        class CustomProvider:
            def translate(self, text, *, source_lang, target_lang, model):
                return text

        assert isinstance(CustomProvider(), TranslationProvider)


# ── OpenAIProvider ────────────────────────────────────────────────


def _make_mock_response(content: str | None = "translated text"):
    """Build a fake OpenAI ChatCompletion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestOpenAIProvider:
    def test_translate_returns_content(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("Hola")
        provider = OpenAIProvider(client=mock_client)

        result = provider.translate(
            "Hello", source_lang="English", target_lang="Spanish", model="gpt-4o"
        )
        assert result == "Hola"

    def test_translate_passes_model_and_messages(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")
        provider = OpenAIProvider(client=mock_client)

        provider.translate(
            "Hi", source_lang="English", target_lang="German", model="gpt-4o"
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "English" in messages[0]["content"]
        assert "German" in messages[0]["content"]
        assert messages[1] == {"role": "user", "content": "Hi"}

    def test_translate_returns_empty_on_none_content(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(None)
        provider = OpenAIProvider(client=mock_client)

        result = provider.translate(
            "Hello", source_lang="English", target_lang="French", model="gpt-4o"
        )
        assert result == ""

    def test_translate_wraps_openai_error(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = OpenAIError("Rate limit")
        provider = OpenAIProvider(client=mock_client)

        with pytest.raises(TranslationError, match="Rate limit"):
            provider.translate(
                "Hello", source_lang="English", target_lang="Spanish", model="gpt-4o"
            )

    def test_lazy_client_uses_get_client(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")

        from ai_pdf_translator import provider as provider_mod

        monkeypatch.setattr(provider_mod, "get_client", lambda: mock_client)

        p = OpenAIProvider()  # no client passed
        p.translate("Hi", source_lang="English", target_lang="Spanish", model="gpt-4o")

        mock_client.chat.completions.create.assert_called_once()


# ── get_provider factory ──────────────────────────────────────────


class TestGetProvider:
    def test_returns_openai_provider_by_default(self):
        provider = get_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_case_insensitive(self):
        provider = get_provider("OpenAI")
        assert isinstance(provider, OpenAIProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown translation provider"):
            get_provider("nonexistent")
