import unittest
import tempfile
import os
from free_vigilance_reduction.entity_recognition.dictionary import Dictionary
from free_vigilance_reduction.entity_recognition.entity import Entity


class TestDictionary(unittest.TestCase):
    def setUp(self):
        self.dict = Dictionary("PER")
        self.dict.add_term("Иван Иванович")
        self.dict.add_term("Иванов Михаил")
        self.dict.add_term("Петр Петров")

    def test_add_term_and_find(self):
        text = "Сегодня Иван Иванович встретился с Иванов Михаил."
        matches = self.dict.find_matches(text)
        self.assertEqual(len(matches), 2)
        self.assertTrue(any(m.text == "Иван Иванович" for m in matches))
        self.assertTrue(any(m.text == "Иванов Михаил" for m in matches))

    def test_find_matches_with_boundaries(self):
        self.dict.add_term("Петр")
        text = "Петруха и Петр Петров пошли в магазин."
        matches = self.dict.find_matches(text)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].text, "Петр Петров")

    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
            temp_file.write("# Комментарий\n")
            temp_file.write("Иван Иванович\n")
            temp_file.write("\n")
            temp_file.write("Мария Петровна\n")
            temp_path = temp_file.name

        test_dict = Dictionary("PER")
        test_dict.load_from_file(temp_path)
        matches = test_dict.find_matches("Там была Иван Иванович и Мария Петровна.")

        os.remove(temp_path)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].text, "Иван Иванович")
        self.assertEqual(matches[1].text, "Мария Петровна")


if __name__ == '__main__':
    unittest.main()
