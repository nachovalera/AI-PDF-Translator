"""Application entry-point for the AI PDF Translator."""

from ai_pdf_translator import build_interface


def main() -> None:
    app = build_interface()
    app.launch()


if __name__ == "__main__":
    main()
