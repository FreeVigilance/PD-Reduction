import unittest
from free_vigilance_reduction.entity_recognition.language_model import LanguageModel
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestLanguageModelMultipleEntities(unittest.TestCase):
    def setUp(self):
        self.model = LanguageModel()
        self.profile = ConfigurationProfile(
            profile_id="test_multi",
            entity_types=["PER", "LOC"]
        )
        self.profile.custom_entity_prompts = {
            "PER": "имена и фамилии людей",
            "LOC": "географические названия: города, страны, улицы"
        }
        self.profile.use_language_model = True
        self.profile.llm_settings = {
            "model_path": "/Users/mikekalabay/models/Vikhr-Gemma-2B-instruct",
            "max_input_tokens": 2000,
            "chunk_overlap_tokens": 150,
            "max_new_tokens": 200,
            "temperature": 0.2
        }

    def test_multiple_entity_types(self):
        text = "Иван Иванович работает в компании Рога и Копыта и живёт в городе Москва."
        entities = self.model.search_entities(text, self.profile)
        self.assertTrue(
            any(e.text == "Иван Иванович" and e.entity_type == "PER" for e in entities),
            "Не найдена Персона"
        )
        self.assertTrue(
            any(e.text == "Москва" and e.entity_type == "LOC" for e in entities),
            "Не найдена Локация"
        )


if __name__ == '__main__':
    unittest.main()