import unittest
import tempfile
import os
import json
from free_vigilance_reduction.reporting.reduction_report import ReductionReport
from free_vigilance_reduction.entity_recognition.entity import Entity


class TestReductionReport(unittest.TestCase):
    def setUp(self):
        self.original_text = "Иван Иванович работает в Газпроме."
        self.reduced_text = "[PERSON] работает в [ORG]."
        self.entities = [
            Entity("Иван Иванович", "PER", 0, 13),
            Entity("Газпроме", "ORG", 25, 33)
        ]
        self.replacements = [
            {"original": "Иван Иванович", "replacement": "[PERSON]", "type": "PER"},
            {"original": "Газпроме", "replacement": "[ORG]", "type": "ORG"}
        ]
        self.report = ReductionReport(
            original_text=self.original_text,
            reduced_text=self.reduced_text,
            entities=self.entities,
            replacements=self.replacements
        )

    def test_to_dict(self):
        result = self.report.to_dict()
        self.assertEqual(result["original_text"], self.original_text)
        self.assertEqual(result["reduced_text"], self.reduced_text)
        self.assertEqual(result["summary"]["replacements_made"], 2)
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(len(result["replacements"]), 2)

    def test_to_json(self):
        json_str = self.report.to_json()
        self.assertIn('"original_text":', json_str)
        self.assertIn('"reduced_text":', json_str)

    def test_save_to_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_path = tmp_file.name

        try:
            self.report.save_to_file(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            with open(tmp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertEqual(data["summary"]["replacements_made"], 2)
                self.assertEqual(len(data["entities"]), 2)
        finally:
            os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
