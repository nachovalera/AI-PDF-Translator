"""Utility helpers for working with the OpenAI client."""

from __future__ import annotations

from openai import OpenAI

from .settings import ensure_api_key


_CLIENT: OpenAI | None = None


def get_client() -> OpenAI:
    """Return a singleton OpenAI client instance."""
    global _CLIENT
    if _CLIENT is None:
        ensure_api_key()
        _CLIENT = OpenAI()
    return _CLIENT


__all__ = ["get_client"]
