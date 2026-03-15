"""Translation provider abstraction layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from openai import OpenAI, OpenAIError

from .openai_client import get_client
from .settings import TRANSLATION_PROVIDER


class TranslationError(Exception):
    """Raised when a translation provider fails."""


@runtime_checkable
class TranslationProvider(Protocol):
    """Interface that any translation backend must satisfy."""

    def translate(
        self,
        text: str,
        *,
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> str:
        """Translate a chunk of text. Returns the translated string."""
        ...


def _build_system_prompt(source_lang: str, target_lang: str) -> str:
    """Build the system prompt used for translation."""
    return (
        "You are a professional translator. Translate the user's text from "
        f"{source_lang} to {target_lang}. Preserve the original structure, lists, "
        "headers, and quotations. Do not add commentary, only provide the translated text."
    )


class OpenAIProvider:
    """TranslationProvider backed by the OpenAI Chat Completions API."""

    def __init__(self, client: OpenAI | None = None) -> None:
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = get_client()
        return self._client

    def translate(
        self,
        text: str,
        *,
        source_lang: str,
        target_lang: str,
        model: str,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _build_system_prompt(source_lang, target_lang)},
                    {"role": "user", "content": text},
                ],
            )
            return response.choices[0].message.content or ""
        except OpenAIError as exc:
            raise TranslationError(str(exc)) from exc


def get_provider(name: str | None = None) -> TranslationProvider:
    """Return a TranslationProvider instance for the given name.

    Falls back to the TRANSLATION_PROVIDER setting (default: 'openai').
    """
    provider_name = (name or TRANSLATION_PROVIDER).lower()
    if provider_name == "openai":
        return OpenAIProvider()
    raise ValueError(
        f"Unknown translation provider: {provider_name!r}. "
        f"Supported providers: 'openai'"
    )


__all__ = [
    "TranslationError",
    "TranslationProvider",
    "OpenAIProvider",
    "_build_system_prompt",
    "get_provider",
]
