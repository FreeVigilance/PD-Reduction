"""
Модуль для распознавания сущностей с использованием регулярных выражений, словарей и языковой модели.
"""

import re
import json
from typing import List
from pathlib import Path

from ..entity_recognition.entity import Entity
from ..config.configuration import ConfigurationProfile
from ..entity_recognition.dictionary_manager import DictionaryManager
from ..entity_recognition.language_model import LanguageModel
from ..utils.logging import get_logger

logger = get_logger(__name__)


class EntityRecognizer:
    """
    Класс для распознавания сущностей в тексте на основе заданного профиля.
    Поддерживает регулярные выражения, словари и языковую модель.
    """

    def __init__(self, regex_path: str = "config/regex_patterns.json"):
        """
        Инициализация EntityRecognizer.

        Args:
            regex_path (str): Путь к файлу с шаблонами регулярных выражений.
        """
        self.dictionary_manager = DictionaryManager()
        self.language_model = LanguageModel()
        self.regex_patterns = self._load_regex_patterns(regex_path)

    def _load_regex_patterns(self, path: str) -> dict:
        """
        Загрузка шаблонов регулярных выражений из JSON-файла.

        Args:
            path (str): Путь к файлу.

        Returns:
            dict: Словарь шаблонов.
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Файл шаблонов не найден: {path}")
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Ошибка при загрузке шаблонов: {exc}")
            return {}

    def detect_entities(self, text: str, profile: ConfigurationProfile) -> List[Entity]:
        """
        Обнаружение сущностей в тексте на основе профиля.

        Args:
            text (str): Текст для анализа.
            profile (ConfigurationProfile): Профиль конфигурации.

        Returns:
            List[Entity]: Найденные сущности.
        """
        entities: List[Entity] = []

        if profile.use_dictionary:
            dictionary_entities = self.dictionary_manager.find_matches(text, profile)
            logger.info(f"Найдено словарных сущностей: {len(dictionary_entities)}")
            for entity_now in dictionary_entities:
                entities.append(entity_now)

        if profile.use_regex:
            regex_entities = self._apply_regex(text, profile)
            logger.info(f"Найдено сущностей по регулярным выражениям: {len(regex_entities)}")
            for entity_now in regex_entities:
                entities.append(entity_now)

        if profile.use_language_model:
            llm_entities = self.language_model.search_entities(text, profile)
            logger.info(f"Найдено сущностей языковой моделью: {len(llm_entities)}")
            for entity_now in llm_entities:
                entities.append(entity_now)

        return self._deduplicate_entities(entities)

    def _apply_regex(self, text: str, profile: ConfigurationProfile) -> List[Entity]:
        """
        Применение регулярных выражений для поиска сущностей.

        Args:
            text (str): Исходный текст.
            profile (ConfigurationProfile): Профиль.

        Returns:
            List[Entity]: Найденные сущности.
        """
        entities = []

        for entity_type in profile.entity_types:
            pattern = self.regex_patterns.get(entity_type)
            if not pattern:
                continue

            for match in re.finditer(pattern, text):
                start, end = match.span()
                entity_text = match.group()
                entity_now = Entity(entity_text, entity_type, start, end)
                entities.append(entity_now)

        return entities

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Удаление перекрывающихся сущностей с приоритетом длинных.

        Args:
            entities (List[Entity]): Список сущностей.

        Returns:
            List[Entity]: Список без перекрытий.
        """
        sorted_entities = sorted(entities, key=lambda entity_now: (entity_now.start_pos, -entity_now.end_pos))
        result = []

        for entity_now in sorted_entities:
            overlap_found = False
            for existing_entity in result:
                if self._overlaps(entity_now, existing_entity):
                    overlap_found = True
                    break
            if not overlap_found:
                result.append(entity_now)

        return result

    @staticmethod
    def _overlaps(entity_now1: Entity, entity_now2: Entity) -> bool:
        """
        Проверка перекрытия двух сущностей.

        Args:
            entity_now1 (Entity)
            entity_now2 (Entity)

        Returns:
            bool: True, если перекрываются.
        """
        return not (entity_now1.end_pos <= entity_now2.start_pos or entity_now1.start_pos >= entity_now2.end_pos)
