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

        self.profile.use_language_model = True
        self.profile.llm_settings = {
            "model_path": "/Users/mikekalabay/models/Vikhr-Gemma-2B-instruct",
            "max_input_tokens": 2000,
            "chunk_overlap_tokens": 150,
            "max_new_tokens": 200,
            "temperature": 0.2
        }

    def test_search_entities(self):
        text = "В конференции принимали участие Иван Иванович и Петр Петров."
        entities = self.model.search_entities(text, self.profile)

        self.assertTrue(
            any(e.text == "Иван Иванович" and e.entity_type == "PER" for e in entities),
            "Не найдена сущность 'Иван Иванович' типа PER"
        )
        self.assertTrue(
            any(e.text == "Петр Петров" and e.entity_type == "PER" for e in entities),
            "Не найдена сущность 'Петр Петров' типа PER"
        )


if __name__ == '__main__':
    unittest.main()