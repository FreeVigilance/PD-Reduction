"""
Модуль для управления словарями.
"""

from typing import Dict, List, Optional
from .dictionary import Dictionary
from ..config.configuration import ConfigurationProfile
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DictionaryManager:
    """
    Класс для управления несколькими словарями.
    """

    def __init__(self) -> None:
        """
        Инициализация менеджера словарей.
        """
        self.dictionaries: Dict[str, Dictionary] = {}
        logger.info("Менеджер словарей инициализирован")

    def load_dictionary(self, name: str, file_path: str, entity_type: str) -> bool:
        """
        Загрузка словаря из файла.

        Args:
            name (str): Имя словаря.
            file_path (str): Путь к файлу.
            entity_type (str): Тип сущности, связанный со словарём.

        Returns:
            bool: True, если успешно, иначе False.
        """
        try:
            dictionary = Dictionary(entity_type)
            dictionary.load_from_file(file_path)
            self.dictionaries[name] = dictionary
            logger.info(f"Словарь '{name}' загружен из {file_path} (тип: {entity_type})")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке словаря '{name}' из {file_path}: {e}")
            return False

    def get_dictionary(self, name: str) -> Optional[Dictionary]:
        """
        Получение словаря по имени.

        Args:
            name (str): Имя словаря.

        Returns:
            Dictionary | None: Объект словаря или None, если не найден.
        """
        return self.dictionaries.get(name)

    def find_matches(self, text: str, profile: Optional[ConfigurationProfile]) -> List:
        """
        Поиск совпадений во всех словарях с учётом профиля.

        Args:
            text (str): Текст для анализа.
            profile (ConfigurationProfile | None): Профиль настроек.

        Returns:
            List[Entity]: Найденные сущности.
        """
        matches = []

        if profile is None or not hasattr(profile, 'dictionary_settings'):
            logger.warning("Профиль не задан или не содержит настроек словарей")
            for name, dictionary in self.dictionaries.items():
                logger.debug(f"Поиск с использованием словаря '{name}' (без фильтрации)")
                matches_from_dict = dictionary.find_matches(text)
                for match in matches_from_dict:
                    matches.append(match)
            return matches

        for dict_name, settings in profile.dictionary_settings.items():
            if not settings.get("enabled", True):
                continue

            dictionary = self.dictionaries.get(dict_name)
            if dictionary is None:
                logger.warning(f"Словарь '{dict_name}' не загружен")
                continue

            dict_matches = dictionary.find_matches(text)

            if hasattr(profile, 'entity_types'):
                filtered = []
                for m in dict_matches:
                    if m.entity_type in profile.entity_types:
                        filtered.append(m)

                if len(filtered) < len(dict_matches):
                    logger.debug(
                        f"Отфильтровано {len(dict_matches) - len(filtered)} сущностей из словаря '{dict_name}'"
                    )

                for match in filtered:
                    matches.append(match)
            else:
                for match in dict_matches:
                    matches.append(match)

        logger.info(f"Обнаружено {len(matches)} сущностей с помощью словарей")
        return matches
