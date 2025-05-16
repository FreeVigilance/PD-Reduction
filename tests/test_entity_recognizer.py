import unittest
from free_vigilance_reduction.entity_recognition.entity_recognizer import EntityRecognizer
from free_vigilance_reduction.config.configuration import ConfigurationProfile
from free_vigilance_reduction.entity_recognition.entity import Entity
import tempfile
import json
import os


class TestEntityRecognizer(unittest.TestCase):
    def setUp(self):
        self.regex_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        regex_data = {
            "DATE": "\\b\\d{1,2}[./-]\\d{1,2}[./-]\\d{2,4}\\b",
            "EMAIL": "[\\w.-]+@[\\w.-]+\\.[a-z]{2,4}"
        }
        json.dump(regex_data, self.regex_file)
        self.regex_file.close()

        self.profile = ConfigurationProfile(
            profile_id="regex_test",
            entity_types=["DATE", "EMAIL"]
        )
        self.profile.use_regex = True
        self.profile.use_dictionary = False
        self.profile.use_language_model = False

        self.recognizer = EntityRecognizer(regex_path=self.regex_file.name)

    def tearDown(self):
        os.unlink(self.regex_file.name)

    def test_regex_detection(self):
        text = "Контакт: test@example.com. Встреча 12/04/2023."
        entities = self.recognizer.detect_entities(text, self.profile)

        self.assertTrue(any(e.text == "test@example.com" and e.entity_type == "EMAIL" for e in entities))
        self.assertTrue(any(e.text == "12/04/2023" and e.entity_type == "DATE" for e in entities))


if __name__ == '__main__':
    unittest.main()
