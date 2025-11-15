from pathlib import Path

from pypdf import PdfReader

from ai_pdf_translator.pdf_utils import chunk_text, text_to_pdf


def test_chunk_text_respects_max_chars():
    paragraph = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    text = "\n".join([paragraph] * 10)

    chunks = chunk_text(text, max_chars=120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 150 for chunk in chunks)


def test_text_to_pdf_creates_pdf_file():
    output_path = text_to_pdf(
        "Hola mundo\n\nEsto es una prueba",
        original_name="demo.pdf",
        source_lang="English",
        target_lang="Spanish",
    )

    pdf_file = Path(output_path)
    assert pdf_file.exists()

    reader = PdfReader(str(pdf_file))
    assert len(reader.pages) >= 1

    pdf_file.unlink()
