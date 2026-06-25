import unittest
from io import BytesIO

from pypdf import PdfWriter

from backend.main import _extract_pdf_text


class PdfExtractTests(unittest.TestCase):
    def test_extract_pdf_text_returns_page_count_when_pymupdf_is_unavailable(self):
        """Windows local env can import pypdf but PyMuPDF/fitz fails with DLL load errors."""
        buf = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(buf)

        text, page_count, truncated = _extract_pdf_text(buf.getvalue(), max_chars=8000)

        self.assertEqual(page_count, 1)
        self.assertFalse(truncated)
        self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main()
