import unittest
from free_vigilance_reduction.entity_recognition.entity import Entity


class TestEntity(unittest.TestCase):
    def test_entity_initialization(self):
        e = Entity("Иван Иванович", "PER", 0, 14)
        self.assertEqual(e.text, "Иван Иванович")
        self.assertEqual(e.entity_type, "PER")
        self.assertEqual(e.start_pos, 0)
        self.assertEqual(e.end_pos, 14)

    def test_str_and_repr(self):
        e = Entity("Москва", "LOC", 10, 16)
        self.assertIn("LOC: 'Москва' (10:16)", str(e))
        self.assertIn("Entity", repr(e))

    def test_to_dict(self):
        e = Entity("ООО Ромашка", "ORG", 20, 32)
        expected = {
            "text": "ООО Ромашка",
            "entity_type": "ORG",
            "start_pos": 20,
            "end_pos": 32
        }
        self.assertEqual(e.to_dict(), expected)

    def test_overlaps_with(self):
        e_now1 = Entity("Петров", "PER", 5, 11)
        e_now2 = Entity("Петр", "PER", 10, 13)
        e_now3 = Entity("Мирный", "PER", 12, 18)
        self.assertTrue(e_now1.overlaps_with(e_now2))
        self.assertFalse(e_now1.overlaps_with(e_now3))

    def test_equality(self):
        e_now1 = Entity("Москва", "LOC", 10, 16)
        e_now2 = Entity("Москва", "LOC", 10, 16)
        e_now3 = Entity("Питер", "LOC", 10, 16)
        self.assertEqual(e_now1, e_now2)
        self.assertNotEqual(e_now1, e_now3)


if __name__ == '__main__':
    unittest.main()
