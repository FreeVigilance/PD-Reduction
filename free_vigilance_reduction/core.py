"""
Основной модуль библиотеки FreeVigilanceReduction, координирующий анонимизацию текста.
"""

from typing import Optional, List
from .config.configuration import ConfigurationManager, ConfigurationProfile
from .documents.document_factory import DocumentFactory
from .entity_recognition.entity_recognizer import EntityRecognizer
from .data_replacement.data_replacer import DataReplacer
from .reporting.reduction_report import ReductionReport
from .reporting.observers import ProcessingObserver
from .utils.logging import get_logger


logger = get_logger(__name__)


class FreeVigilanceReduction:
    """
    Основной класс библиотеки анонимизации, объединяющий все компоненты.

    Координирует загрузку конфигурации, обработку документов и тек
    ста, распознавание сущностей, замену данных и генерацию отчётов.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        regex_path: str = "config/regex_patterns.json"
    ):
        """
        Инициализация компонентов системы.

        Args:
            config_path (str | None): Путь к JSON-файлу с профилями.
            regex_path (str): Путь к файлу с шаблонами регулярных выражений.
        """
        logger.info("Инициализация FreeVigilanceReduction")

        self.config_manager = ConfigurationManager(config_path)
        self.document_factory = DocumentFactory()
        self.entity_recognizer = EntityRecognizer(regex_path)
        self.data_replacer = DataReplacer()
        self.observers: List[ProcessingObserver] = []

        logger.info("FreeVigilanceReduction успешно инициализирована")

    def add_observer(self, observer_now: ProcessingObserver) -> None:
        """
        Добавление наблюдателя для получения событий обработки.

        Args:
            observer_now (ProcessingObserver): Наблюдатель события.
        """
        self.observers.append(observer_now)

    def _notify(self, event_now: str, data_now: dict) -> None:
        """
        Уведомление всех зарегистрированных наблюдателей о событии.

        Args:
            event_now (str): Название события.
            data_now (dict): Сопутствующие данные события.
        """
        for observer in self.observers:
            observer.update(event_now, data_now)

    def process_file(
        self,
        file_path_now: str,
        profile_id: str
    ) -> ReductionReport:
        """
        Анонимизация и сохранение документа из файла.

        Args:
            file_path_now (str): Путь к исходному файлу.
            profile_id (str): Идентификатор профиля обработки.

        Returns:
            ReductionReport: Отчёт о произведённых изменениях.
        """
        logger.info(f"Анонимизация файла '{file_path_now}' с профилем '{profile_id}'")
        self._notify("start", {"file_path": file_path_now, "profile_id": profile_id})


        profile_now: ConfigurationProfile = self.config_manager.get_profile(profile_id)
        document_now = self.document_factory.create_document(file_path_now)
        text_now = document_now.get_text()
        self._notify("text_extracted", {"text": text_now})


        entities_now = self.entity_recognizer.detect_entities(text_now, profile_now)
        self._notify("entities_detected", {"entities": entities_now})

        reduced_text_now, replacements_now = self.data_replacer.reduce_text(
            text_now,
            entities_now,
            profile_now
        )
        self._notify("text_reduced", {"reduced_text": reduced_text_now, "replacements": replacements_now})

        document_now.create_redacted_copy(reduced_text_now)
        self._notify("document_saved", {"file_path": document_now.file_path})

        report_now = ReductionReport(
            text_now,
            reduced_text_now,
            entities_now,
            replacements_now
        )
        self._notify("report_generated", {"report": report_now})

        return report_now

    def reduce_text(
        self,
        text_now: str,
        profile_id: Optional[str] = None
    ) -> ReductionReport:
        """
        Анонимизация произвольного текста (без файловой обёртки).

        Args:
            text_now (str): Текст для анонимизации.
            profile_id (str | None): Идентификатор профиля (по умолчанию — default).

        Returns:
            ReductionReport: Отчёт об анонимизации текста.
        """
        profile_now: ConfigurationProfile = self.config_manager.get_profile(profile_id)
        logger.info(f"Анонимизация текста с профилем '{profile_now.profile_id}'")
        self._notify("start", {"text": text_now, "profile_id": profile_now.profile_id})

        entities_now = self.entity_recognizer.detect_entities(text_now, profile_now)
        self._notify("entities_detected", {"entities": entities_now})

        reduced_text_now, replacements_now = self.data_replacer.reduce_text(
            text_now,
            entities_now,
            profile_now
        )
        self._notify("text_reduced", {"reduced_text": reduced_text_now, "replacements": replacements_now})

        report_now = ReductionReport(
            original_text=text_now,
            anonymized_text=reduced_text_now,
            entities=entities_now,
            replacements=replacements_now
        )
        self._notify("report_generated", {"report": report_now})

        return report_now
