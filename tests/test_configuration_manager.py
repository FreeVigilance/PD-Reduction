import unittest
import tempfile
import os
import json
from free_vigilance_reduction.config.configuration import ConfigurationManager, ConfigurationProfile


class TestConfigurationManager(unittest.TestCase):
    def setUp(self):
        self.profile_1 = ConfigurationProfile(
            profile_id="profile1",
            entity_types=["PER"],
            replacement_rules={"PER": "template"},
            dictionary_paths={"PER": "/tmp/per_dict.txt"},
            custom_entity_prompts={"PER": "люди"},
            use_regex=True,
            use_dictionary=True,
            use_language_model=False
        )

        self.profile_2 = ConfigurationProfile(
            profile_id="profile2",
            entity_types=["ORG"],
            replacement_rules={"ORG": "stars"},
            dictionary_paths={"ORG": "/tmp/org_dict.txt"},
            custom_entity_prompts={"ORG": "организации"},
            use_regex=False,
            use_dictionary=True,
            use_language_model=True
        )

        self.tempfile = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tempfile.close()

    def tearDown(self):
        os.remove(self.tempfile.name)

    def test_add_and_get_profile(self):
        manager = ConfigurationManager()
        manager.add_profile(self.profile_1)
        manager.add_profile(self.profile_2)
        
        self.assertEqual(manager.get_profile("profile1").profile_id, "profile1")
        self.assertEqual(manager.get_profile("profile2").get_replacement_strategy("ORG"), "stars")

    def test_set_and_get_default_profile(self):
        manager = ConfigurationManager()
        manager.add_profile(self.profile_1)
        manager.set_default_profile("profile1")
        default = manager.get_profile()
        self.assertEqual(default.profile_id, "profile1")

    def test_save_and_load_profiles(self):
        manager = ConfigurationManager()
        manager.add_profile(self.profile_1)
        manager.add_profile(self.profile_2)
        manager.set_default_profile("profile2")
        manager.save_profiles(self.tempfile.name)

        new_manager = ConfigurationManager(self.tempfile.name)
        self.assertEqual(set(new_manager.get_profile_list()), {"profile1", "profile2"})
        self.assertEqual(new_manager.get_profile().profile_id, "profile2")

    def test_validate_all(self):
        manager = ConfigurationManager()
        manager.add_profile(self.profile_1)
        manager.add_profile(self.profile_2)
        manager.validate_all()

    def test_missing_profile_raises(self):
        manager = ConfigurationManager()
        with self.assertRaises(KeyError):
            manager.get_profile("unknown")


if __name__ == '__main__':
    unittest.main()
