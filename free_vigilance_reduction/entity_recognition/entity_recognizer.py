"""
Модуль для распознавания сущностей с использованием регулярных выражений,
словари и языковой модели.
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

    Поддерживает три источника для обнаружения сущностей:
      - регулярные выражения (regex)
      - пользовательские словари (dictionary)
      - языковую модель (LLM)

    Для каждого профиля выполняет последовательное применение включённых
    методов и объединяет результаты с удалением дублирующих и перекрывающихся
    сущностей.
    """

    def __init__(self, regex_path: str = "config/regex_patterns.json"):
        """
        Инициализация EntityRecognizer.

        Args:
            regex_path (str): Путь к JSON-файлу с шаблонами регулярных выражений.
        """
        self.dictionary_manager = DictionaryManager()
        self.language_model = LanguageModel()
        self.regex_patterns = self._load_regex_patterns(regex_path)

    def _load_regex_patterns(self, path: str) -> dict:
        """
        Загрузка шаблонов регулярных выражений из JSON-файла.

        Args:
            path (str): Путь к файлу с шаблонами.

        Returns:
            dict: Словарь {entity_type: regex_pattern}.
        """
        p = Path(path)
        if not p.exists():
            logger.warning(f"Файл шаблонов не найден: {path}")
            return {}

        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Ошибка при парсинге шаблонов regex: {exc}")
            return {}

    def detect_entities(
        self,
        text: str,
        profile: ConfigurationProfile
    ) -> List[Entity]:
        """
        Обнаружение сущностей в тексте согласно профилю.

        Args:
            text (str): Исходный текст для анализа.
            profile (ConfigurationProfile): Профиль конфигурации.

        Returns:
            List[Entity]: Список найденных сущностей без перекрытий.
        """
        entities: List[Entity] = []

        if profile.use_dictionary:
            dict_entities = self.dictionary_manager.find_matches(text, profile)
            logger.info(f"Найдено словарных сущностей: {len(dict_entities)}")
            entities.extend(dict_entities)

        if profile.use_regex:
            regex_entities = self._apply_regex(text, profile)
            logger.info(f"Найдено сущностей по regex: {len(regex_entities)}")
            entities.extend(regex_entities)

        if profile.use_language_model:
            llm_entities = self.language_model.search_entities(text, profile)
            logger.info(f"Найдено сущностей LLM: {len(llm_entities)}")
            entities.extend(llm_entities)

        unique = self._deduplicate_entities(entities)
        logger.info(f"Всего после дедупликации: {len(unique)}")
        return unique

    def _apply_regex(
        self,
        text: str,
        profile: ConfigurationProfile
    ) -> List[Entity]:
        """
        Применение регулярных выражений для поиска сущностей.

        Args:
            text (str): Текст для поиска.
            profile (ConfigurationProfile): Профиль с enabled_entity_types.

        Returns:
            List[Entity]: Найденные сущности.
        """
        found: List[Entity] = []
        for etype in profile.entity_types:
            pattern = self.regex_patterns.get(etype)
            if not pattern:
                continue
            for m in re.finditer(pattern, text):
                ent = Entity(m.group(), etype, m.start(), m.end())
                found.append(ent)
        return found

    def _deduplicate_entities(
        self,
        entities: List[Entity]
    ) -> List[Entity]:
        """
        Удаление перекрывающихся и дублирующихся сущностей.

        Приоритет отдается более длинным сущностям при совпадающих границах.

        Args:
            entities (List[Entity]): Сырые найденные сущности.

        Returns:
            List[Entity]: Фильтрованный список сущностей.
        """
        sorted_ents = sorted(
            entities,
            key=lambda e: (e.start_pos, -(e.end_pos - e.start_pos))
        )
        result: List[Entity] = []
        for ent in sorted_ents:
            if not any(self._overlaps(ent, ex) for ex in result):
                result.append(ent)
        return result

    @staticmethod
    def _overlaps(a: Entity, b: Entity) -> bool:
        """
        Проверка перекрытия двух сущностей.

        Args:
            a (Entity), b (Entity)

        Returns:
            bool: True, если сущности перекрываются.
        """
        return not (a.end_pos <= b.start_pos or a.start_pos >= b.end_pos)
