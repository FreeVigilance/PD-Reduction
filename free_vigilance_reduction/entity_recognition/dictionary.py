"""
Модуль для работы со словарями терминов.
"""

from typing import Dict, List
from .entity import Entity


class Dictionary:
    """
    Класс для хранения и поиска терминов в тексте.
    """

    def __init__(self, entity_type: str):
        """
        Инициализация словаря для конкретного типа сущностей.

        Args:
            entity_type (str): Тип сущности, для которого создаётся словарь (например, PER).
        """
        self.entity_type: str = entity_type
        self.terms: List[str] = []
        self.index: Dict[str, List[str]] = {}

    def add_term(self, term: str) -> None:
        """
        Добавление термина в словарь.

        Args:
            term (str): Термин для добавления.
        """
        term = term.strip()
        if not term:
            return
        if term in self.terms:
            return

        self.terms.append(term)
        first = term[0].lower()
        if first not in self.index:
            self.index[first] = []
        self.index[first].append(term)

    def find_matches(self, text: str) -> List[Entity]:
        """
        Поиск всех вхождений сущностий в тексте.

        Args:
            text (str): Текст для анализа.

        Returns:
            list: Найденные сущности.
        """
        if not text:
            return []

        matches: List[Entity] = []
        text_lower = text.lower()
        i = 0
        while i < len(text):
            char = text_lower[i]
            if char in self.index:
                for term in self.index[char]:
                    term_len = len(term)
                    if i + term_len <= len(text):
                        fragment = text_lower[i:i + term_len]
                        if fragment == term.lower():
                            before_ok = i == 0 or not text_lower[i - 1].isalnum()
                            after_ok = i + term_len == len(text) or not text_lower[i + term_len].isalnum()
                            if before_ok and after_ok:
                                original = text[i:i + term_len]
                                matches.append(Entity(original, self.entity_type, i, i + term_len))
                                i += term_len - 1
                                break
            i += 1
        return matches

    def load_from_file(self, file_path: str) -> "Dictionary":
        """
        Загрузка сущностей из файла.

        Args:
            file_path (str): Путь к файлу словаря.

        Returns:
            Dictionary: Текущий объект.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.add_term(line)
        except Exception as e:
            print(f"Ошибка при загрузке словаря из {file_path}: {e}")
        return self
