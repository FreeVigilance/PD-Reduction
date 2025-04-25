"""
Модуль для представления обнаруженных сущностей в тексте.
"""

from typing import Dict


class Entity:
    """
    Класс для представления обнаруженной сущности в тексте.
    """

    def __init__(self, text: str, entity_type: str, start_pos: int, end_pos: int):
        """
        Инициализация сущности.

        Args:
            text (str): Текст сущности.
            entity_type (str): Тип сущности.
            start_pos (int): Начальная позиция в тексте.
            end_pos (int): Конечная позиция в тексте.
        """
        self.text: str = text
        self.entity_type: str = entity_type
        self.start_pos: int = start_pos
        self.end_pos: int = end_pos

    def __str__(self) -> str:
        """
        Строковое представление сущности.

        Returns:
            str: Строковое представление сущности.
        """
        return f"{self.entity_type}: '{self.text}' ({self.start_pos}:{self.end_pos})"

    def __repr__(self) -> str:
        """
        Представление сущности для отладки.

        Returns:
            str: Представление сущности для отладки.
        """
        return f"Entity({self.text!r}, {self.entity_type!r}, {self.start_pos}, {self.end_pos})"

    def __eq__(self, other: object) -> bool:
        """
        Проверка на равенство двух сущностей.

        Args:
            other (object): Объект для сравнения.

        Returns:
            bool: True, если равны.
        """
        if not isinstance(other, Entity):
            return False
        return (
            self.text == other.text
            and self.entity_type == other.entity_type
            and self.start_pos == other.start_pos
            and self.end_pos == other.end_pos
        )

    def to_dict(self) -> Dict[str, object]:
        """
        Преобразование сущности в словарь.

        Returns:
            dict: Словарь с данными сущности.
        """
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos
        }

    def overlaps_with(self, other: "Entity") -> bool:
        """
        Проверка перекрытия с другой сущностью.

        Args:
            other (Entity): Другая сущность.

        Returns:
            bool: True, если сущности перекрываются, иначе False.
        """
        return self.start_pos <= other.end_pos and self.end_pos >= other.start_pos