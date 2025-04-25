"""
Классы для управления конфигурацией системы анонимизации.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurationProfile:
    """
    Профиль конфигурации для анонимизации текста.
    """

    def __init__(
        self,
        profile_id: str,
        entity_types: Optional[List[str]] = None,
        replacement_rules: Optional[Dict[str, str]] = None,
        dictionary_paths: Optional[Dict[str, str]] = None,
        custom_entity_prompts: Optional[Dict[str, str]] = None,
        use_regex: bool = True,
        use_dictionary: bool = True,
        use_language_model: bool = True,
        llm_settings=None
    ):
        """
        Инициализация профиля конфигурации.

        Args:
            profile_id (str): Уникальный идентификатор профиля.
            entity_types (List[str], optional): Список типов сущностей.
            replacement_rules (Dict[str, str], optional): Правила замены по типу.
            dictionary_paths (Dict[str, str], optional): Пути к словарям.
            custom_entity_prompts (Dict[str, str], optional): Промпты для LLM.
            use_regex (bool): Включить ли поиск по regex.
            use_dictionary (bool): Включить ли словари.
            use_language_model (bool): Включить ли LLM.
            llm_settings: Настройки языковой модели.
        """
        self.profile_id = profile_id
        self.entity_types = entity_types or []
        self.replacement_rules = replacement_rules or {}
        self.dictionary_paths = dictionary_paths or {}
        self.custom_entity_prompts = custom_entity_prompts or {}

        self.use_regex = use_regex
        self.use_dictionary = use_dictionary
        self.use_language_model = use_language_model
        self.llm_settings = llm_settings or {}

        self.created_at = None
        self.updated_at = None

    def to_dict(self) -> Dict:
        """
        Преобразует профиль в словарь.

        Returns:
            dict: Словарь со всеми настройками.
        """
        profile_dict = {
            "profile_id": self.profile_id,
            "enabled_entity_types": self.entity_types,
            "replacement_rules": self.replacement_rules,
            "dictionary_paths": self.dictionary_paths,
            "custom_entity_prompts": self.custom_entity_prompts,
            "use_regex": self.use_regex,
            "use_dictionary": self.use_dictionary,
            "use_language_model": self.use_language_model,
            "llm_settings": self.llm_settings,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        return profile_dict

    def save_to_file(self, file_path: str) -> None:
        """
        Сохраняет профиль в файл JSON.

        Args:
            file_path (str): Путь к файлу.
        """
        self.updated_at = self._current_timestamp()
        if self.created_at is None:
            self.created_at = self.updated_at

        profile_path_now = Path(file_path)
        if not profile_path_now.parent.exists():
            profile_path_now.parent.mkdir(parents=True)

        with open(profile_path_now, 'w', encoding='utf-8') as file_now:
            json.dump(self.to_dict(), file_now, ensure_ascii=False, indent=4)

        logger.info(f"Профиль конфигурации сохранён в {file_path}")

    @staticmethod
    def from_dict(data: Dict) -> "ConfigurationProfile":
        """
        Создание профиля из словаря.

        Args:
            data (dict): Словарь с данными профиля.

        Returns:
            ConfigurationProfile: Загруженный профиль.
        """
        return ConfigurationProfile(
            profile_id=data["profile_id"],
            entity_types=data.get("enabled_entity_types", []),
            replacement_rules=data.get("replacement_rules", {}),
            dictionary_paths=data.get("dictionary_paths", {}),
            custom_entity_prompts=data.get("custom_entity_prompts", {}),
            use_regex=data.get("use_regex", True),
            use_dictionary=data.get("use_dictionary", True),
            use_language_model=data.get("use_language_model", True),
            llm_settings=data.get("llm_settings", {})
        )

    @staticmethod
    def from_file(file_path: str) -> "ConfigurationProfile":
        """
        Загрузка профиля из файла.

        Args:
            file_path (str): Путь к JSON-файлу.

        Returns:
            ConfigurationProfile: Загруженный профиль.
        """
        path_now = Path(file_path)
        if not path_now.exists():
            logger.error(f"Файл профиля не найден: {file_path}")
            raise FileNotFoundError(f"Файл профиля не найден: {file_path}")

        with open(path_now, 'r', encoding='utf-8') as file_now:
            data_now = json.load(file_now)

        profile_now = ConfigurationProfile.from_dict(data_now)
        profile_now.created_at = data_now.get("created_at")
        profile_now.updated_at = data_now.get("updated_at")
        return profile_now

    def validate(self) -> None:
        """
        Проверяет наличие правил замены для всех включённых сущностей.

        Raises:
            ValueError: Если отсутствует правило замены.
        """
        missing_now = []
        for entity_type_now in self.entity_types:
            if entity_type_now not in self.replacement_rules:
                missing_now.append(entity_type_now)

        if missing_now:
            message_now = f"Ошибка валидации: отсутствуют правила замены для сущностей: {', '.join(missing_now)}"
            logger.error(message_now)
            raise ValueError(message_now)

    def _current_timestamp(self) -> str:
        """
        Текущее время в формате ISO.

        Returns:
            str: Дата и время.
        """
        from datetime import datetime
        return datetime.now().isoformat()

    def get_replacement_strategy(self, entity_type: str) -> Optional[str]:
        """
        Получение метода замены по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Optional[str]: Метод замены (template, stars, remove).
        """
        return self.replacement_rules.get(entity_type)

    def get_dictionary_path(self, entity_type: str) -> Optional[str]:
        """
        Получение пути к словарю по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Optional[str]: Путь к словарю.
        """
        return self.dictionary_paths.get(entity_type)

    def get_custom_prompt(self, entity_type: str) -> Optional[str]:
        """
        Получение кастомного промпта по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Optional[str]: Промпт для LLM.
        """
        return self.custom_entity_prompts.get(entity_type)


class ConfigurationManager:
    """
    Менеджер для управления несколькими конфигурационными профилями.
    """

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.profiles: Dict[str, ConfigurationProfile] = {}
        self.default_profile_id: Optional[str] = None

        if config_file_path:
            self.load_profiles(config_file_path)

    def add_profile(self, profile_now: ConfigurationProfile) -> None:
        """
        Добавление нового профиля.

        Args:
            profile_now (ConfigurationProfile): Профиль для добавления.
        """
        profile_now.validate()
        self.profiles[profile_now.profile_id] = profile_now
        logger.info(f"Добавлен профиль: {profile_now.profile_id}")

    def get_profile(self, profile_id: Optional[str] = None) -> ConfigurationProfile:
        """
        Получение профиля по ID или по умолчанию.

        Args:
            profile_id (str, optional): ID профиля.

        Returns:
            ConfigurationProfile: Найденный профиль.
        """
        if profile_id is None:
            if self.default_profile_id is None:
                raise ValueError("Не установлен профиль по умолчанию.")
            profile_id = self.default_profile_id

        if profile_id not in self.profiles:
            raise KeyError(f"Профиль '{profile_id}' не найден.")

        return self.profiles[profile_id]

    def set_default_profile(self, profile_id_now: str) -> None:
        """
        Установка профиля по умолчанию.

        Args:
            profile_id_now (str): ID профиля для установки по умолчанию.
        """
        if profile_id_now not in self.profiles:
            raise KeyError(f"Профиль '{profile_id_now}' не найден для установки по умолчанию.")
        self.default_profile_id = profile_id_now
        logger.info(f"Установлен профиль по умолчанию: {profile_id_now}")

    def load_profiles(self, file_path_now: str) -> None:
        """
        Загрузка профилей из JSON-файла.

        Args:
            file_path_now (str): Путь к файлу конфигурации.
        """
        config_path = Path(file_path_now)
        if not config_path.exists():
            logger.warning(f"Файл конфигурации не найден: {file_path_now}")
            return

        with open(config_path, 'r', encoding='utf-8') as config_file_now:
            data_now = json.load(config_file_now)

        for profile_data_now in data_now.get("profiles", []):
            profile_now = ConfigurationProfile.from_dict(profile_data_now)
            self.profiles[profile_now.profile_id] = profile_now

        self.default_profile_id = data_now.get("default_profile_id")
        logger.info(f"Загружено профилей: {len(self.profiles)}")

    def save_profiles(self, file_path_now: Optional[str] = None) -> None:
        """
        Сохранение всех профилей в JSON-файл.

        Args:
            file_path_now (str, optional): Путь к файлу.
        """
        file_path_now = file_path_now or self.config_file_path
        if not file_path_now:
            raise ValueError("Не указан путь к файлу конфигурации.")

        data_to_save = {
            "profiles": [],
            "default_profile_id": self.default_profile_id
        }

        for profile_now in self.profiles.values():
            profile_dict_now = profile_now.to_dict()
            data_to_save["profiles"].append(profile_dict_now)

        save_path = Path(file_path_now)
        if not save_path.parent.exists():
            save_path.parent.mkdir(parents=True)

        with open(save_path, 'w', encoding='utf-8') as out_file_now:
            json.dump(data_to_save, out_file_now, ensure_ascii=False, indent=4)

        logger.info(f"Конфигурация сохранена в файл: {file_path_now}")

    def get_profile_list(self) -> List[str]:
        """
        Получить список ID всех загруженных профилей.

        Returns:
            List[str]: Идентификаторы профилей.
        """
        profile_ids_now = []
        for profile_id_now in self.profiles.keys():
            profile_ids_now.append(profile_id_now)
        return profile_ids_now

    def validate_all(self) -> None:
        """
        Валидация всех профилей в менеджере.

        Raises:
            ValueError: Если хоть один профиль невалиден.
        """
        for profile_now in self.profiles.values():
            profile_now.validate()
