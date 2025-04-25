"""
Модуль для замены обнаруженных сущностей в тексте.
"""

from typing import Dict, List, Tuple
from ..entity_recognition.entity import Entity
from ..config.configuration import ConfigurationProfile


class DataReplacer:
    """
    Класс для замены обнаруженных сущностей в тексте в соответствии с правилами профиля конфигурации.
    """

    def reduce_text(
        self,
        text: str,
        entities: List[Entity],
        profile: ConfigurationProfile
    ) -> Tuple[str, List[Dict]]:
        """
        Выполняет замену сущностей в тексте в соответствии с настройками профиля.

        Args:
            text (str): Исходный текст.
            entities (List[Entity]): Список сущностей для замены.
            profile (ConfigurationProfile): Профиль конфигурации с правилами замены.

        Returns:
            Tuple[str, List[Dict]]: Текст после замены и список замен.
        """
        entities_sorted = sorted(entities, key=lambda e: e.start_pos, reverse=True)
        replacements = []

        for entity in entities_sorted:
            rule = profile.replacement_rules.get(entity.entity_type)
            if not rule:
                continue

            rule_type = rule.get("type")
            if rule_type == "template":
                replacement = rule.get("template", f"[{entity.entity_type}]")
            elif rule_type == "stars":
                replacement = "*" * len(entity.text)
            elif rule_type == "remove":
                replacement = ""
            else:
                continue
            space = ""
            if entity.end_pos < len(text) and text[entity.end_pos] != ' ' and replacement:
                space = " "

            prefix = text[:entity.start_pos]
            suffix = text[entity.end_pos:]
            text = prefix + replacement + space + suffix

            replacements.append({
                "original": entity.text,
                "replacement": replacement,
                "entity_type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos
            })

        return text, replacements
