"""Tests for ai_pdf_translator.provider module."""

from __future__ import annotations

from unittest.mock import MagicMock

import anthropic as anthropic_sdk
import pytest
from openai import OpenAIError

from ai_pdf_translator.provider import (
    AnthropicProvider,
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

    def test_anthropic_provider_satisfies_protocol(self):
        provider = AnthropicProvider(client=MagicMock())
        assert isinstance(provider, TranslationProvider)

    def test_custom_class_satisfies_protocol(self):
        class CustomProvider:
            def translate(self, text, *, source_lang, target_lang, model):
                return text

        assert isinstance(CustomProvider(), TranslationProvider)


# ── OpenAIProvider ────────────────────────────────────────────────


def _make_mock_openai_response(content: str | None = "translated text"):
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
        mock_client.chat.completions.create.return_value = _make_mock_openai_response("Hola")
        provider = OpenAIProvider(client=mock_client)

        result = provider.translate(
            "Hello", source_lang="English", target_lang="Spanish", model="gpt-4o"
        )
        assert result == "Hola"

    def test_translate_passes_model_and_messages(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response("ok")
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
        mock_client.chat.completions.create.return_value = _make_mock_openai_response(None)
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
        mock_client.chat.completions.create.return_value = _make_mock_openai_response("ok")

        from ai_pdf_translator import provider as provider_mod

        monkeypatch.setattr(provider_mod, "get_client", lambda: mock_client)

        p = OpenAIProvider()  # no client passed
        p.translate("Hi", source_lang="English", target_lang="Spanish", model="gpt-4o")

        mock_client.chat.completions.create.assert_called_once()

    def test_has_default_model(self):
        assert OpenAIProvider.default_model is not None
        assert isinstance(OpenAIProvider.default_model, str)


# ── AnthropicProvider ─────────────────────────────────────────────


def _make_mock_anthropic_response(text: str = "translated text"):
    """Build a fake Anthropic Messages response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


class TestAnthropicProvider:
    def test_translate_returns_content(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_anthropic_response("Hola")
        provider = AnthropicProvider(client=mock_client)

        result = provider.translate(
            "Hello", source_lang="English", target_lang="Spanish", model="claude-haiku-4-5-20251001"
        )
        assert result == "Hola"

    def test_translate_passes_model_system_and_user(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_anthropic_response("ok")
        provider = AnthropicProvider(client=mock_client)

        provider.translate(
            "Hi", source_lang="English", target_lang="German", model="claude-haiku-4-5-20251001"
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert "English" in call_kwargs["system"]
        assert "German" in call_kwargs["system"]
        assert call_kwargs["messages"] == [{"role": "user", "content": "Hi"}]

    def test_translate_wraps_anthropic_error(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic_sdk.APIError(
            message="Rate limit", request=MagicMock(), body=None
        )
        provider = AnthropicProvider(client=mock_client)

        with pytest.raises(TranslationError):
            provider.translate(
                "Hello", source_lang="English", target_lang="Spanish", model="claude-haiku-4-5-20251001"
            )

    def test_lazy_client_uses_get_anthropic_client(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_anthropic_response("ok")

        from ai_pdf_translator import provider as provider_mod

        monkeypatch.setattr(provider_mod, "get_anthropic_client", lambda: mock_client)

        p = AnthropicProvider()  # no client passed
        p.translate("Hi", source_lang="English", target_lang="Spanish", model="claude-haiku-4-5-20251001")

        mock_client.messages.create.assert_called_once()

    def test_has_default_model(self):
        assert AnthropicProvider.default_model is not None
        assert isinstance(AnthropicProvider.default_model, str)


# ── get_provider factory ──────────────────────────────────────────


class TestGetProvider:
    def test_returns_openai_provider_by_default(self):
        provider = get_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_case_insensitive(self):
        provider = get_provider("OpenAI")
        assert isinstance(provider, OpenAIProvider)

    def test_returns_anthropic_provider(self):
        provider = get_provider("anthropic")
        assert isinstance(provider, AnthropicProvider)

    def test_anthropic_case_insensitive(self):
        provider = get_provider("Anthropic")
        assert isinstance(provider, AnthropicProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown translation provider"):
            get_provider("nonexistent")

    def test_error_message_lists_supported_providers(self):
        with pytest.raises(ValueError, match="openai"):
            get_provider("bad")
        with pytest.raises(ValueError, match="anthropic"):
            get_provider("bad")


# ── Provider contract tests (Task #6) ────────────────────────────


def _make_openai_provider_with_mock():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_openai_response("translated")
    return OpenAIProvider(client=mock_client)


def _make_anthropic_provider_with_mock():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_anthropic_response("translated")
    return AnthropicProvider(client=mock_client)


@pytest.mark.parametrize(
    "provider_factory",
    [_make_openai_provider_with_mock, _make_anthropic_provider_with_mock],
    ids=["openai", "anthropic"],
)
class TestProviderContract:
    """Contract tests: every provider must satisfy the same behavioural guarantees."""

    def test_satisfies_translation_provider_protocol(self, provider_factory):
        provider = provider_factory()
        assert isinstance(provider, TranslationProvider)

    def test_translate_returns_non_empty_string(self, provider_factory):
        provider = provider_factory()
        result = provider.translate(
            "Hello", source_lang="English", target_lang="Spanish", model="any-model"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_translate_raises_translation_error_on_api_failure(self, provider_factory):
        """Any API-level exception must be re-raised as TranslationError."""
        provider = provider_factory()
        # Replace the underlying client's API method with one that raises
        if isinstance(provider, OpenAIProvider):
            provider.client.chat.completions.create.side_effect = OpenAIError("fail")
        else:
            provider.client.messages.create.side_effect = anthropic_sdk.APIError(
                message="fail", request=MagicMock(), body=None
            )
        with pytest.raises(TranslationError):
            provider.translate(
                "Hello", source_lang="English", target_lang="Spanish", model="any-model"
            )

    def test_translate_accepts_required_keyword_args(self, provider_factory):
        """Ensure the signature matches the protocol (source_lang, target_lang, model)."""
        provider = provider_factory()
        # Should not raise TypeError
        provider.translate("text", source_lang="English", target_lang="French", model="m")

    def test_has_default_model_attribute(self, provider_factory):
        provider = provider_factory()
        assert hasattr(provider, "default_model")
        assert isinstance(provider.default_model, str)
