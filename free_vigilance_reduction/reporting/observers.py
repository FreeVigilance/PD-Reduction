"""
Модуль с интерфейсами и реализациями наблюдателей (обсерверов) для процесса анонимизации.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..reporting.reduction_report import ReductionReport
from ..entity_recognition.entity import Entity
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProcessingObserver(ABC):
    """
    Абстрактный наблюдатель за этапами обработки текста.
    Используется для отслеживания прогресса и логирования.
    """

    @abstractmethod
    def on_process_start(self, document: Optional[str] = None, text: Optional[str] = None) -> None:
        """
        Вызывается при старте процесса анонимизации.

        Args:
            document (str, optional): Путь к файлу документа, если используется файл.
            text (str, optional): Исходный текст, если используется строка.
        """
        pass

    @abstractmethod
    def on_entities_detected(self, entities: List[Entity]) -> None:
        """
        Вызывается после обнаружения сущностей.

        Args:
            entities (List[Entity]): Найденные сущности.
        """
        pass

    @abstractmethod
    def on_text_reduced(self, reduced_text: str) -> None:
        """
        Вызывается после выполнения замены сущностей в тексте.

        Args:
            reduced_text (str): Обработанный текст.
        """
        pass

    @abstractmethod
    def on_process_complete(self, report: ReductionReport) -> None:
        """
        Вызывается по завершении всего процесса анонимизации.

        Args:
            report (ReductionReport): Отчёт о проделанной работе.
        """
        pass

    @abstractmethod
    def on_error(self, error: Exception) -> None:
        """
        Вызывается при возникновении ошибки в процессе обработки.

        Args:
            error (Exception): Исключение, описывающее ошибку.
        """
        pass


class ConsoleObserver(ProcessingObserver):
    """
    Реализация наблюдателя, выводящего информацию о ходе обработки в консоль.
    """

    def on_process_start(self, document: Optional[str] = None, text: Optional[str] = None) -> None:
        if document:
            print(f"Начата обработка документа: {document}")
        elif text:
            print(f"Начата обработка текста (длина: {len(text)} символов)")

    def on_entities_detected(self, entities: List[Entity]) -> None:
        print(f"Обнаружено сущностей: {len(entities)}")
        for entity in entities[:5]:
            print(f"  - {entity}")
        if len(entities) > 5:
            print(f"  ... и еще {len(entities) - 5} сущностей")

    def on_text_reduced(self, reduced_text: str) -> None:
        preview = reduced_text[:100] + "..." if len(reduced_text) > 100 else reduced_text
        print(f"Результат анонимизации (превью): {preview}")

    def on_process_complete(self, report: ReductionReport) -> None:
        print(f"Анонимизация завершена. Всего замен: {report.reduction_count}")

    def on_error(self, error: Exception) -> None:
        print(f"[ОШИБКА] {str(error)}")


class LoggingObserver(ProcessingObserver):
    """
    Реализация наблюдателя, записывающего ход обработки в лог.
    """

    def __init__(self, logger_instance=None):
        """
        Инициализация LoggingObserver.

        Args:
            logger_instance (Logger, optional): Пользовательский логгер, если требуется.
        """
        self.logger = logger_instance or logger

    def on_process_start(self, document: Optional[str] = None, text: Optional[str] = None) -> None:
        if document:
            self.logger.info(f"Обработка документа начата: {document}")
        elif text:
            self.logger.info(f"Обработка текста начата (длина: {len(text)} символов)")

    def on_entities_detected(self, entities: List[Entity]) -> None:
        self.logger.info(f"Обнаружено сущностей: {len(entities)}")
        for entity in entities:
            self.logger.debug(f"Сущность: {entity}")

    def on_text_reduced(self, reduced_text: str) -> None:
        self.logger.info(f"Анонимизированный текст сформирован (длина: {len(reduced_text)})")

    def on_process_complete(self, report: ReductionReport) -> None:
        self.logger.info(f"Анонимизация завершена. Всего замен: {report.reduction_count}")

    def on_error(self, error: Exception) -> None:
        self.logger.error(f"Произошла ошибка при обработке: {str(error)}", exc_info=True)
