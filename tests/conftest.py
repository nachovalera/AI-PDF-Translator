import sys
from pathlib import Path

import pytest
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_pdf(path: Path, text: str) -> Path:
    """Create a minimal PDF containing *text* at *path*."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    width = pdf.w - 2 * pdf.l_margin
    for line in text.splitlines():
        pdf.multi_cell(width, 10, line or " ")
    pdf.output(str(path))
    return path


@pytest.fixture()
def make_pdf(tmp_path: Path):
    """Factory fixture: call ``make_pdf("some text")`` to get a temp PDF path."""
    created: list[Path] = []

    def _factory(text: str = "Hello world\nThis is a test", name: str = "sample.pdf") -> Path:
        path = tmp_path / name
        _write_pdf(path, text)
        created.append(path)
        return path

    yield _factory


@pytest.fixture()
def sample_pdf(make_pdf):
    """Pre-built temp PDF with standard test content."""
    return make_pdf("Hello world\n\nThis is paragraph two.\n\nThird paragraph here.")
