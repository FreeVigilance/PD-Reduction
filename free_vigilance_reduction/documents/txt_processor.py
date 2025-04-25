"""
Обработчик текстовых (.txt) документов.
"""

from .base import Document
from pathlib import Path


class TxtProcessor(Document):
    """
    Класс для работы с .txt документами.
    """

    def get_text(self) -> str:
        """
        Извлекает текст из .txt файла.

        Returns:
            str: Содержимое файла.
        """
        path = Path(self.file_path)
        with open(path, 'r', encoding='utf-8') as file:
            self.text_content = file.read()
        return self.text_content

    def create_redacted_copy(self, reduced_text: str) -> None:
        """
        Создаёт анонимизированную копию .txt документа.

        Args:
            reduced_text (str): Текст после замены сущностей.
        """
        redacted_path = Path(self.file_path).with_name(Path(self.file_path).stem + "_redacted.txt")
        with open(redacted_path, 'w', encoding='utf-8') as file:
            file.write(reduced_text)
        self.metadata['redacted_path'] = str(redacted_path)
