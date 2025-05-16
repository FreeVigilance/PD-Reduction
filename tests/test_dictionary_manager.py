import unittest
import tempfile
import os
from free_vigilance_reduction.entity_recognition.dictionary_manager import DictionaryManager
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestDictionaryManager(unittest.TestCase):
    def setUp(self):
        self.manager = DictionaryManager()

        fd, self.temp_path = tempfile.mkstemp(suffix=".txt", text=True)
        os.close(fd)
        with open(self.temp_path, "w", encoding="utf-8") as f:
            f.write("Иван Иванович\nИванов Михаил\n")

        self.manager.load_dictionary("test_dict", self.temp_path, "PER")
        self.profile = ConfigurationProfile(
            profile_id="test",
            entity_types=["PER"],
        )
        self.profile.dictionary_settings = {
            "test_dict": {"enabled": True, "path": self.temp_path}
        }

    def tearDown(self):
        os.remove(self.temp_path)

    def test_get_dictionary(self):
        dictionary = self.manager.get_dictionary("test_dict")
        self.assertIsNotNone(dictionary)
        self.assertEqual(dictionary.entity_type, "PER")

    def test_find_matches_with_profile(self):
        text = "Иванов Михаил пошел в магазин."
        matches = self.manager.find_matches(text, self.profile)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].text, "Иванов Михаил")
        self.assertEqual(matches[0].entity_type, "PER")

    def test_find_matches_no_profile(self):
        matches = self.manager.find_matches("Иван Иванович приехал.", None)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].text, "Иван Иванович")


if __name__ == '__main__':
    unittest.main()