import unittest
import tempfile
import os
from free_vigilance_reduction.entity_recognition.dictionary_manager import DictionaryManager
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestDictionaryManager(unittest.TestCase):
    def setUp(self):
        self.manager = DictionaryManager()

        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
        self.temp_file.write("Иван Иванович\nИванов Михаил\n")
        self.temp_file.close()

        self.manager.load_dictionary("test_dict", self.temp_file.name, "PER")

        self.profile = ConfigurationProfile(
            profile_id="test",
            entity_types=["PER"],
        )
        self.profile.dictionary_settings = {
            "test_dict": {"enabled": True, "path": self.temp_file.name}
        }

    def tearDown(self):
        os.remove(self.temp_file.name)

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
