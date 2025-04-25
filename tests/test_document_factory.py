import unittest
from free_vigilance_reduction.documents.document_factory import DocumentFactory
from free_vigilance_reduction.documents.txt_processor import TxtProcessor
from free_vigilance_reduction.documents.pdf_processor import PdfProcessor
from free_vigilance_reduction.documents.docx_processor import DocxProcessor


class TestDocumentFactory(unittest.TestCase):
    def setUp(self):
        self.factory = DocumentFactory()

    def test_txt_creation(self):
        doc = self.factory.create_document("sample.txt")
        self.assertIsInstance(doc, TxtProcessor)

    def test_pdf_creation(self):
        doc = self.factory.create_document("sample.pdf")
        self.assertIsInstance(doc, PdfProcessor)

    def test_docx_creation(self):
        doc = self.factory.create_document("sample.docx")
        self.assertIsInstance(doc, DocxProcessor)

    def test_unsupported_extension(self):
        with self.assertRaises(ValueError):
            self.factory.create_document("sample.xls")

    def test_supported_formats(self):
        formats = self.factory.get_supported_formats()
        self.assertIn(".txt", formats)
        self.assertIn(".pdf", formats)
        self.assertIn(".docx", formats)


if __name__ == '__main__':
    unittest.main()
