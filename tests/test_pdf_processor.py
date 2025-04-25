import unittest
import tempfile
import os
from free_vigilance_reduction.documents.pdf_processor import PdfProcessor
from PyPDF2 import PdfWriter


class TestPdfProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with open(self.temp_file.name, 'wb') as f:
            writer.write(f)
        self.processor = PdfProcessor(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)
        redacted_path = self.processor.metadata.get('redacted_path')
        if redacted_path and os.path.exists(redacted_path):
            os.unlink(redacted_path)

    def test_get_text_empty(self):
        text = self.processor.get_text()
        self.assertEqual(text.strip(), "")

    def test_create_redacted_copy(self):
        redacted_text = "Персональные данные удалены."
        self.processor.create_redacted_copy(redacted_text)
        redacted_path = self.processor.metadata['redacted_path']
        self.assertTrue(os.path.exists(redacted_path))


if __name__ == '__main__':
    unittest.main()