"""Utility helpers for working with the Anthropic client."""

from __future__ import annotations

import anthropic

from .settings import ensure_anthropic_api_key


_CLIENT: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Return a singleton Anthropic client instance."""
    global _CLIENT
    if _CLIENT is None:
        ensure_anthropic_api_key()
        _CLIENT = anthropic.Anthropic()
    return _CLIENT


__all__ = ["get_client"]
