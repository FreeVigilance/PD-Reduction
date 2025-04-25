"""
Основной модуль библиотеки FreeVigilanceReduction, координирующий анонимизацию текста.
"""

from .config.configuration import ConfigurationManager, ConfigurationProfile
from .documents.document_factory import DocumentFactory
from .entity_recognition.entity_recognizer import EntityRecognizer
from .data_replacement.data_replacer import DataReplacer
from .reporting.reduction_report import ReductionReport
from .reporting.observers import ProcessingObserver
from .utils.logging import get_logger
from typing import Optional, List

logger = get_logger(__name__)


class FreeVigilanceReduction:
    """
    Основной класс библиотеки анонимизации, объединяющий все компоненты.
    """

    def __init__(self, config_path: Optional[str] = None, regex_path: str = "config/regex_patterns.json"):
        """
        Инициализация всех компонентов системы.

        Args:
            config_path (str | None): Путь к конфигурационному JSON-файлу.
            regex_path (str): Путь к JSON-файлу с шаблонами регулярных выражений.
        """
        logger.info("Инициализация FreeVigilanceReduction")

        self.config_manager = ConfigurationManager(config_path)
        self.document_factory = DocumentFactory()
        self.entity_recognizer = EntityRecognizer(regex_path=regex_path)
        self.data_replacer = DataReplacer()
        self.observers: List[ProcessingObserver] = []

        logger.info("FreeVigilanceReduction успешно инициализирован")

    def add_observer(self, observer_now: ProcessingObserver) -> None:
        """
        Добавление наблюдателя обработки.

        Args:
            observer_now (ProcessingObserver): Объект-наблюдатель.
        """
        self.observers.append(observer_now)

    def _notify(self, event_now: str, data_now: dict) -> None:
        """
        Уведомление всех наблюдателей о событии.

        Args:
            event_now (str): Название события.
            data_now (dict): Сопутствующие данные.
        """
        for observer_now in self.observers:
            observer_now.update(event_now, data_now)

    def process_file(self, file_path_now: str, profile_id: str) -> ReductionReport:
        """
        Обработка файла с анонимизацией данных.

        Args:
            file_path_now (str): Путь к обрабатываемому файлу.
            profile_id (str): Идентификатор профиля конфигурации.

        Returns:
            ReductionReport: Отчёт о редактировании.
        """
        logger.info(f"Анонимизация файла {file_path_now} с профилем {profile_id}")
        self._notify("start", {"file_path": file_path_now, "profile_id": profile_id})

        profile_now: ConfigurationProfile = self.config_manager.get_profile(profile_id)
        document_now = self.document_factory.create_document(file_path_now)
        text_now = document_now.get_text()

        self._notify("text_extracted", {"text": text_now})

        entities_now = self.entity_recognizer.detect_entities(text_now, profile_now)
        self._notify("entities_detected", {"entities": entities_now})

        reduced_text_now, replacements_now = self.data_replacer.reduce_text(text_now, entities_now, profile_now)
        self._notify("text_reduced", {"reduced_text": reduced_text_now, "replacements": replacements_now})

        document_now.create_redacted_copy(reduced_text_now)
        self._notify("document_saved", {"file_path": document_now.file_path})

        report_now = ReductionReport(text_now, reduced_text_now, entities_now, replacements_now)
        self._notify("report_generated", {"report": report_now})

        return report_now

    def reduce_text(self, text_now: str, profile_id: Optional[str] = None) -> ReductionReport:
        """
        Обработка текста напрямую (не из файла).

        Args:
            text_now (str): Текст для обработки.
            profile_id (str | None): Идентификатор профиля (по умолчанию — профиль по умолчанию).

        Returns:
            ReductionReport: Отчёт об анонимизации текста.
        """
        logger.info(f"Анонимизация текста с профилем {profile_id}")

        if profile_id:
            profile_now = self.config_manager.get_profile(profile_id)
        else:
            profile_now = self.config_manager.get_default_profile()

        self._notify("start", {"text": text_now, "profile_id": profile_id})

        entities_now = self.entity_recognizer.detect_entities(text_now, profile_now)
        self._notify("entities_detected", {"entities": entities_now})

        reduced_text_now, replacements_now = self.data_replacer.reduce_text(text_now, entities_now, profile_now)
        self._notify("text_reduced", {"reduced_text": reduced_text_now, "replacements": replacements_now})

        report_now = ReductionReport(text_now, reduced_text_now, entities_now, replacements_now)
        self._notify("report_generated", {"report": report_now})

        return report_now
