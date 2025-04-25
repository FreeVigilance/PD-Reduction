
import unittest
import os
import shutil
from pathlib import Path
from free_vigilance_reduction.entity_recognition.entity_recognizer import EntityRecognizer
from free_vigilance_reduction.data_replacement.data_replacer import DataReplacer
from free_vigilance_reduction.config.configuration import ConfigurationProfile

class TestDataReplacerIntegrated(unittest.TestCase):
    def setUp(self):
        self.text = "Иван Иванович работает в Газпром и живёт в Москве. Телефон: +7 (495) 123-45-67."

        self.profile = ConfigurationProfile(
            profile_id="test",
            entity_types=["PER", "ORG", "PHONE"]
        )

        self.profile.replacement_rules = {
            "PER": {"type": "template", "template": "[PERSON]"},
            "ORG": {"type": "stars"},
            "PHONE": {"type": "remove"}
        }

        self.profile.custom_entity_prompts = {
            "PER": "имена и фамилии людей",
            "ORG": "названия организаций",
            "PHONE": "телефонные номера в любом формате"
        }

        self.profile.use_dictionary = True
        self.profile.use_regex = True
        self.profile.use_language_model = False

        self.profile.dictionary_settings = {
            "PER": {"enabled": True, "path": "tests/resources/per_dict.txt"},
            "ORG": {"enabled": True, "path": "tests/resources/org_dict.txt"}
        }

        self.regex_path = "tests/resources/regex_patterns.json"
        Path("tests/resources/").mkdir(parents=True, exist_ok=True)

        with open("tests/resources/per_dict.txt", "w", encoding="utf-8") as f:
            f.write("Иван Иванович\n")
        with open("tests/resources/org_dict.txt", "w", encoding="utf-8") as f:
            f.write("Газпром\n")
        with open(self.regex_path, 'w', encoding='utf-8') as f:
            f.write('{"PHONE": "\\\\+7 \\\\([0-9]{3}\\\\) [0-9]{3}-[0-9]{2}-[0-9]{2}"}')

        self.recognizer = EntityRecognizer(regex_path=self.regex_path)
        for name, settings in self.profile.dictionary_settings.items():
            if settings.get("enabled", True):
                self.recognizer.dictionary_manager.load_dictionary(
                    name=name,
                    file_path=settings["path"],
                    entity_type=name
                )

        self.replacer = DataReplacer()

    def tearDown(self):
        shutil.rmtree("tests/resources/", ignore_errors=True)

    def test_replace_entities_end_to_end(self):
        entities = self.recognizer.detect_entities(self.text, self.profile)
        print(entities)
        reduced_text, _ = self.replacer.reduce_text(self.text, entities, self.profile)

        print("\n[DEBUG OUTPUT] Финальный текст:")
        print(reduced_text)

        self.assertIn("[PERSON]", reduced_text)
        self.assertIn("*******", reduced_text)
        self.assertNotIn("+7", reduced_text)
        self.assertTrue(reduced_text.endswith("."))

if __name__ == "__main__":
    unittest.main()
