"""
Классы для управления конфигурацией системы анонимизации.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurationProfile:
    """
    Профиль конфигурации для анонимизации текста.

    Хранит все параметры обработки:
      - Разрешенные типы сущностей
      - Правила замены
      - Пути к пользовательским словарям
      - Промпты для LLM
      - Флаги включения механизмов (regex, словарь, LLM)
      - Настройки языковой модели (llm_settings)

    llm_settings должен содержать ключи:
      - model_path (str): путь к локальной папке или файлу модели
      - device (str): 'cpu' или 'cuda'/'cuda:0'
      - max_input_tokens (int): максимальное число входных токенов
      - chunk_overlap_tokens (int): число токенов перекрытия при разбиении
      - max_new_tokens (int): максимальное число генерируемых токенов
      - temperature (float): параметр температуры при генерации
    """

    def __init__(
        self,
        profile_id: str,
        entity_types: Optional[List[str]] = None,
        replacement_rules: Optional[Dict[str, Any]] = None,
        dictionary_paths: Optional[Dict[str, Any]] = None,
        custom_entity_prompts: Optional[Dict[str, str]] = None,
        use_regex: bool = True,
        use_dictionary: bool = True,
        use_language_model: bool = True,
        llm_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализация профиля конфигурации.

        Args:
            profile_id (str): Уникальный идентификатор профиля.
            entity_types (List[str], optional): Список типов сущностей.
            replacement_rules (Dict[str, Any], optional): Правила замены по типу.
            dictionary_paths (Dict[str, Any], optional): Пути к словарям.
            custom_entity_prompts (Dict[str, str], optional): Промпты для LLM.
            use_regex (bool): Включить ли поиск по regex.
            use_dictionary (bool): Включить ли поиск по словарю.
            use_language_model (bool): Включить ли LLM.
            llm_settings (Dict[str, Any], optional): Настройки языковой модели.
        """
        self.profile_id = profile_id
        self.entity_types = entity_types or []
        self.replacement_rules = replacement_rules or {}
        self.dictionary_paths = dictionary_paths or {}
        self.custom_entity_prompts = custom_entity_prompts or {}

        self.use_regex = use_regex
        self.use_dictionary = use_dictionary
        self.use_language_model = use_language_model
        self.llm_settings = llm_settings.copy() if llm_settings else {}
        self.llm_settings.setdefault("model_path", "")
        self.llm_settings.setdefault("device", "cpu")
        self.llm_settings.setdefault("max_input_tokens", 512)
        self.llm_settings.setdefault("chunk_overlap_tokens", 0)
        self.llm_settings.setdefault("max_new_tokens", 256)
        self.llm_settings.setdefault("temperature", 0.5)

        self.created_at = None
        self.updated_at = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует профиль в словарь для сериализации.

        Returns:
            dict: Словарь со всеми настройками.
        """
        return {
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

    def save_to_file(self, file_path: str) -> None:
        """
        Сохраняет профиль в файл JSON.

        Args:
            file_path (str): Путь к выходному JSON-файлу.
        """
        self.updated_at = self._current_timestamp()
        if self.created_at is None:
            self.created_at = self.updated_at

        path = Path(file_path)
        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(self.to_dict(), fp, ensure_ascii=False, indent=4)

        logger.info(f"Профиль конфигурации '{self.profile_id}' сохранён в {file_path}")

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConfigurationProfile":
        """
        Создание профиля из словаря, загруженного из JSON.

        Args:
            data (dict): Словарь с данными профиля.

        Returns:
            ConfigurationProfile: Инстанс профиля.
        """
        profile = ConfigurationProfile(
            profile_id=data.get("profile_id", ""),
            entity_types=data.get("enabled_entity_types", []),
            replacement_rules=data.get("replacement_rules", {}),
            dictionary_paths=data.get("dictionary_paths", {}),
            custom_entity_prompts=data.get("custom_entity_prompts", {}),
            use_regex=data.get("use_regex", True),
            use_dictionary=data.get("use_dictionary", True),
            use_language_model=data.get("use_language_model", True),
            llm_settings=data.get("llm_settings", {})
        )
        profile.created_at = data.get("created_at")
        profile.updated_at = data.get("updated_at")
        return profile

    @staticmethod
    def from_file(file_path: str) -> "ConfigurationProfile":
        """
        Загрузка одного профиля из JSON-файла.

        Args:
            file_path (str): Путь к файлу.

        Returns:
            ConfigurationProfile: Загруженный профиль.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Файл профиля не найден: {file_path}")
            raise FileNotFoundError(f"Файл профиля не найден: {file_path}")

        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)

        return ConfigurationProfile.from_dict(data)

    def validate(self) -> None:
        """
        Проверяет целостность профиля:
         - Наличие правил замены для всех типов сущностей
         - Корректность LLM-настроек (непустой model_path и неотрицательные токены)
        """
        missing = [t for t in self.entity_types if t not in self.replacement_rules]
        if missing:
            msg = f"Отсутствуют правила замены для сущностей: {', '.join(missing)}"
            logger.error(msg)
            raise ValueError(msg)

        if self.use_language_model:
            path = self.llm_settings.get("model_path", "")
            if not path or not Path(path).exists():
                msg = f"Некорректный путь до модели LLM: '{path}'"
                logger.error(msg)
                raise ValueError(msg)
            for key in ("max_input_tokens", "chunk_overlap_tokens", "max_new_tokens"):
                val = self.llm_settings.get(key)
                if not isinstance(val, int) or val < 0:
                    msg = f"LLM-настройка '{key}' должна быть неотрицательным целым, получено: {val}"
                    logger.error(msg)
                    raise ValueError(msg)
            temp = self.llm_settings.get("temperature")
            if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 1.0):
                msg = f"LLM-настройка 'temperature' должна быть от 0.0 до 1.0, получено: {temp}"
                logger.error(msg)
                raise ValueError(msg)

    def _current_timestamp(self) -> str:
        """
        Возвращает текущее время в формате ISO.

        Returns:
            str: Строка с датой и временем.
        """
        from datetime import datetime
        return datetime.now().isoformat()

    def get_replacement_strategy(self, entity_type: str) -> Optional[Any]:
        """
        Получение метода замены по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Any: Правило замены (template, remove, stars и т.п.).
        """
        return self.replacement_rules.get(entity_type)

    def get_dictionary_path(self, entity_type: str) -> Optional[str]:
        """
        Получение пути к словарю по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Optional[str]: Путь к словарю или None.
        """
        return self.dictionary_paths.get(entity_type)

    def get_custom_prompt(self, entity_type: str) -> Optional[str]:
        """
        Получение кастомного промпта для LLM по типу сущности.

        Args:
            entity_type (str): Тип сущности.

        Returns:
            Optional[str]: Строка промпта или None.
        """
        return self.custom_entity_prompts.get(entity_type)


class ConfigurationManager:
    """
    Менеджер для загрузки и управления несколькими конфигурационными профилями.
    """

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.profiles: Dict[str, ConfigurationProfile] = {}
        self.default_profile_id: Optional[str] = None

        if config_file_path:
            self.load_profiles(config_file_path)

    def add_profile(self, profile: ConfigurationProfile) -> None:
        """
        Добавление нового профиля в менеджер.

        Args:
            profile (ConfigurationProfile): Инстанс профиля.
        """
        profile.validate()
        self.profiles[profile.profile_id] = profile
        logger.info(f"Профиль '{profile.profile_id}' добавлен.")

    def get_profile(self, profile_id: Optional[str] = None) -> ConfigurationProfile:
        """
        Получение профиля по ID или по умолчанию.

        Args:
            profile_id (str, optional): Идентификатор профиля.

        Returns:
            ConfigurationProfile: Соответствующий профиль.
        """
        if profile_id is None:
            if self.default_profile_id is None:
                raise ValueError("Не задан профиль по умолчанию.")
            profile_id = self.default_profile_id

        if profile_id not in self.profiles:
            raise KeyError(f"Профиль '{profile_id}' не найден.")

        return self.profiles[profile_id]

    def set_default_profile(self, profile_id: str) -> None:
        """
        Установка профиля по умолчанию.

        Args:
            profile_id (str): Идентификатор существующего профиля.
        """
        if profile_id not in self.profiles:
            raise KeyError(f"Профиль '{profile_id}' не найден для установки.")
        self.default_profile_id = profile_id
        logger.info(f"Профиль по умолчанию установлен: '{profile_id}'.")

    def load_profiles(self, file_path_now: str) -> None:
        """
        Загрузка профилей из JSON-конфига.

        Args:
            file_path_now (str): Путь к файлу конфигурации.
        """
        path = Path(file_path_now)
        if not path.exists():
            logger.warning(f"Файл конфигурации не найден: {file_path_now}")
            return

        try:
            raw_text = path.read_text(encoding='utf-8')
        except Exception as exc:
            logger.error(f"Не удалось прочитать файл конфигурации '{file_path_now}': {exc}")
            return

        lines = raw_text.splitlines()
        clean_lines = [ln for ln in lines if not ln.strip().startswith("//")]
        clean_json = "\n".join(clean_lines)

        try:
            data = json.loads(clean_json)
        except json.JSONDecodeError as exc:
            logger.error(f"Ошибка разбора JSON в файле '{file_path_now}': {exc}")
            return

        for profile_data in data.get("profiles", []):
            profile = ConfigurationProfile.from_dict(profile_data)
            self.profiles[profile.profile_id] = profile

        self.default_profile_id = data.get("default_profile_id")
        logger.info(f"Загружены профили: {list(self.profiles.keys())}")

    def save_profiles(self, file_path: Optional[str] = None) -> None:
        """
        Сохранение всех профилей в JSON-файл.

        Args:
            file_path (str, optional): Путь к файлу (если None — используется исходный)."""
        path = Path(file_path or self.config_file_path or "")
        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        data = {
            "profiles": [p.to_dict() for p in self.profiles.values()],
            "default_profile_id": self.default_profile_id
        }
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)

        logger.info(f"Конфигурация сохранена: {path}")

    def get_profile_list(self) -> List[str]:
        """
        Список доступных профилей.

        Returns:
            List[str]: Список идентификаторов профилей.
        """
        return list(self.profiles.keys())

    def validate_all(self) -> None:
        """
        Валидация всех загруженных профилей.

        Raises:
            ValueError: Если хоть один профиль невалиден.
        """
        for profile in self.profiles.values():
            profile.validate()
