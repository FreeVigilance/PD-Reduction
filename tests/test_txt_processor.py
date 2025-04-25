import unittest
import tempfile
import os
from free_vigilance_reduction.documents.txt_processor import TxtProcessor


class TestTxtProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w+', encoding='utf-8')
        self.temp_file.write("Это пример текста для анонимизации.")
        self.temp_file.close()
        self.processor = TxtProcessor(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)
        if os.path.exists(self.processor.metadata.get('redacted_path', '')):
            os.unlink(self.processor.metadata['redacted_path'])

    def test_get_text(self):
        text = self.processor.get_text()
        self.assertEqual(text, "Это пример текста для анонимизации.")

    def test_create_redacted_copy(self):
        redacted_text = "[REDACTED TEXT]"
        self.processor.create_redacted_copy(redacted_text)

        redacted_path = self.processor.metadata['redacted_path']
        self.assertTrue(os.path.exists(redacted_path))
        with open(redacted_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, redacted_text)


if __name__ == '__main__':
    unittest.main()