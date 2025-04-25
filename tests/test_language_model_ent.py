import unittest
from free_vigilance_reduction.entity_recognition.language_model import LanguageModel
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestLanguageModelMultipleEntities(unittest.TestCase):
    def setUp(self):
        self.model = LanguageModel()
        self.profile = ConfigurationProfile(
            profile_id="test_multi",
            entity_types=["PER", "LOC", "ORG"]
        )
        self.profile.custom_entity_prompts = {
            "PER": "имена и фамилии людей",
            "LOC": "географические названия: города, страны, улицы",
            "ORG": "названия организаций и компаний"
        }

    def test_multiple_entity_types(self):
        text = "Иван Иванович работает в компании Рога и Копыта и живёт в городе Москва."
        entities = self.model.search_entities(text, self.profile)

        print("\n[DEBUG OUTPUT] Найденные сущности:")
        for entity in entities:
            print(f"{entity}")

        self.assertTrue(any(e.text == "Иван Иванович" and e.entity_type == "PER" for e in entities))
        self.assertTrue(any(e.text == "Рога и Копыта" and e.entity_type == "ORG" for e in entities))
        self.assertTrue(any(e.text == "Москва" and e.entity_type == "LOC" for e in entities))


if __name__ == '__main__':
    unittest.main()
