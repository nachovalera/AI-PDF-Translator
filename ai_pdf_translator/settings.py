"""Global configuration and constants for the translator app."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


ROOT_DIR = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT_DIR / "fonts" / "DejaVuSans.ttf"
PDF_OUTPUT_DIR = ROOT_DIR / "translated_pdfs"
DEFAULT_MODEL = os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-5-mini")
MAX_CHARS_PER_CHUNK = int(os.getenv("MAX_CHARS_PER_CHUNK", 3500))
TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "openai")


def ensure_api_key() -> None:
    """Raise a helpful error when the OpenAI API key is missing."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Please configure your .env file.")


__all__ = [
    "ROOT_DIR",
    "FONT_PATH",
    "PDF_OUTPUT_DIR",
    "DEFAULT_MODEL",
    "MAX_CHARS_PER_CHUNK",
    "TRANSLATION_PROVIDER",
    "ensure_api_key",
]
