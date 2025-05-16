import unittest
from free_vigilance_reduction.core import FreeVigilanceReduction
from free_vigilance_reduction.config.configuration import ConfigurationProfile
import tempfile
import os
import json


class TestFreeVigilanceReduction(unittest.TestCase):
    def setUp(self):
        self.regex_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        json.dump({"PER": r"\bИван Иванович\b"}, self.regex_file)
        self.regex_file.close()

        self.config_path = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json').name
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

        self.engine = FreeVigilanceReduction(
            config_path=self.config_path,
            regex_path=self.regex_file.name
        )

        self.profile = ConfigurationProfile(profile_id="test_profile")
        self.profile.entity_types = ["PER"]
        self.profile.replacement_rules = {
            "PER": {"type": "template", "template": "[PERSON]"}
        }
        self.profile.use_regex = True
        self.profile.use_dictionary = False
        self.profile.use_language_model = False

        self.engine.config_manager.profiles["test_profile"] = self.profile
        self.engine.config_manager.save_profiles()

    def tearDown(self):
        os.unlink(self.regex_file.name)
        os.unlink(self.config_path)

    def test_process_text_via_file(self):
        text = "Иван Иванович работает в Газпроме."
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            report = self.engine.process_file(tmp_path, profile_id="test_profile")

            self.assertIn("[PERSON]", report.reduced_text)
            self.assertEqual(len(report.entities), 1)
            self.assertEqual(report.entities[0].text, "Иван Иванович")
        finally:
            os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()