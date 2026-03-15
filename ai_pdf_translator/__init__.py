"""Core package for the AI PDF Translator app."""

from .interface import build_interface
from .provider import TranslationError, TranslationProvider, get_provider
from .translation_service import translate_pdf

__all__ = [
    "build_interface",
    "translate_pdf",
    "TranslationError",
    "TranslationProvider",
    "get_provider",
]
