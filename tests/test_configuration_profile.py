import unittest
import tempfile
import json
import os
from free_vigilance_reduction.config.configuration import ConfigurationProfile


class TestConfigurationProfile(unittest.TestCase):
    def setUp(self):
        self.sample_profile = ConfigurationProfile(
            profile_id="test_profile",
            entity_types=["PER", "ORG"],
            replacement_rules={
                "PER": "template",
                "ORG": "stars"
            },
            dictionary_paths={
                "PER": "/tmp/per_dict.txt",
                "ORG": "/tmp/org_dict.txt"
            },
            custom_entity_prompts={
                "PER": "ФИО сотрудников",
                "ORG": "названия организаций"
            },
            use_regex=True,
            use_dictionary=True,
            use_language_model=False
        )

    def test_to_dict_and_from_dict(self):
        data = self.sample_profile.to_dict()
        restored = ConfigurationProfile.from_dict(data)
        self.assertEqual(restored.profile_id, "test_profile")
        self.assertIn("PER", restored.entity_types)
        self.assertEqual(restored.get_replacement_strategy("ORG"), "stars")
        self.assertEqual(restored.get_dictionary_path("ORG"), "/tmp/org_dict.txt")
        self.assertFalse(restored.use_language_model)

    def test_save_and_load_profile(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name
            self.sample_profile.save_to_file(temp_path)

        loaded = ConfigurationProfile.from_file(temp_path)
        self.assertEqual(loaded.profile_id, self.sample_profile.profile_id)
        self.assertEqual(loaded.entity_types, self.sample_profile.entity_types)
        os.remove(temp_path)

    def test_validate_success(self):
        self.sample_profile.validate()

    def test_validate_missing_rule(self):
        profile = ConfigurationProfile(
            profile_id="bad_profile",
            entity_types=["PER", "LOC"],
            replacement_rules={"PER": "template"}
        )
        with self.assertRaises(ValueError):
            profile.validate()


if __name__ == '__main__':
    unittest.main()
