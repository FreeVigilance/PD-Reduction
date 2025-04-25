"""
Абстрактный базовый класс для документов.
"""

from abc import ABC, abstractmethod
from typing import Dict


class Document(ABC):
    """
    Абстрактный класс, представляющий документ.
    Содержит интерфейс для извлечения текста и создания анонимизированной копии.
    """

    def __init__(self, file_path: str):
        """
        Инициализация документа.

        Args:
            file_path (str): Путь к файлу документа.
        """
        self.file_path: str = file_path
        self.text_content: str = ""
        self.metadata: Dict = {}

    @abstractmethod
    def get_text(self) -> str:
        """
        Извлечение текста из документа.

        Returns:
            str: Извлечённый текст.
        """
        pass

    @abstractmethod
    def create_redacted_copy(self, reduced_text: str) -> None:
        """
        Создание анонимизированной копии документа на основе заменённого текста.

        Args:
            reduced_text (str): Текст после анонимизации.
        """
        pass
