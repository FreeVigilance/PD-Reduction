"""
Фабрика для создания обработчиков документов по расширению файла.
"""

import os
from typing import Type, Dict
from .base import Document
from .txt_processor import TxtProcessor
from .pdf_processor import PdfProcessor
from .docx_processor import DocxProcessor


class DocumentFactory:
    """
    Класс-фабрика для создания документов соответствующего типа.
    Поддерживает расширения: .txt, .pdf, .docx.
    """

    def __init__(self):
        """Инициализация фабрики с регистрацией доступных обработчиков."""
        self.processors: Dict[str, Type[Document]] = {
            ".txt": TxtProcessor,
            ".pdf": PdfProcessor,
            ".docx": DocxProcessor
        }

    def create_document(self, file_path: str) -> Document:
        """
        Создание экземпляра документа по расширению файла.

        Args:
            file_path (str): Путь к файлу документа.

        Returns:
            Document: Обработчик документа соответствующего типа.

        Raises:
            ValueError: Если расширение файла не поддерживается.
        """
        ext = os.path.splitext(file_path)[-1].lower()
        if ext not in self.processors:
            raise ValueError(f"Unsupported file extension: {ext}")

        return self.processors[ext](file_path)

    def get_supported_formats(self):
        """
        Получение списка поддерживаемых расширений файлов.

        Returns:
            List[str]: Список расширений.
        """
        return list(self.processors.keys())
