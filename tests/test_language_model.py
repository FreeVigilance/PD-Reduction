import unittest
from free_vigilance_reduction.entity_recognition.language_model import LanguageModel
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestLanguageModel(unittest.TestCase):
    def setUp(self):
        self.model = LanguageModel()
        self.profile = ConfigurationProfile(
            profile_id="test_profile",
            entity_types=["PER"],
        )
        self.profile.custom_entity_prompts = {
            "PER": "имена и фамилии людей"
        }

    def test_search_entities(self):
        text = "В конференции принимали участие Иван Иванович и Петр Петров."
        entities = self.model.search_entities(text, self.profile)

        print("\n[DEBUG OUTPUT] Найденные сущности:")
        for entity in entities:
            print(f"{entity}")

        self.assertTrue(any(e.text == "Иван Иванович" and e.entity_type == "PER" for e in entities))
        self.assertTrue(any(e.text == "Петр Петров" and e.entity_type == "PER" for e in entities))


if __name__ == '__main__':
    unittest.main()
