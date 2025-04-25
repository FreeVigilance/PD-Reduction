"""
Модуль для создания отчетов о результатах анонимизации.
"""

import json
import csv
import os
from typing import List, Dict, Tuple
from pathlib import Path
from ..entity_recognition.entity import Entity
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ReductionReport:
    """
    Класс для создания и сохранения отчетов о результатах анонимизации текста.
    """

    def __init__(
        self,
        original_text: str,
        reduced_text: str,
        entities: List[Entity],
        replacements: List[Dict]
    ) -> None:
        """
        Инициализация отчета.

        Args:
            original_text (str): Исходный текст.
            reduced_text (str): Анонимизированный текст.
            entities (List[Entity]): Найденные сущности.
            replacements (List[Dict]): Список с информацией о произведенных заменах.
        """
        self.original_text = original_text
        self.reduced_text = reduced_text
        self.entities = entities
        self.replacements = replacements
        self.reduction_count = len(replacements)

        logger.info(f"Создан отчет: {self.reduction_count} замен")

    def to_dict(self) -> Dict:
        """
        Преобразование отчета в словарь.

        Returns:
            dict: Представление отчета в виде словаря.
        """
        return {
            "original_text": self.original_text,
            "reduced_text": self.reduced_text,
            "summary": {
                "original_length": len(self.original_text),
                "reduced_length": len(self.reduced_text),
                "entities_found": len(self.entities),
                "replacements_made": self.reduction_count
            },
            "entities": [e.to_dict() for e in self.entities],
            "replacements": self.replacements
        }


    def to_json(self) -> str:
        """
        Преобразование отчета в JSON-строку.

        Returns:
            str: JSON-представление отчета.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)

    def save_to_file(self, file_path: str) -> None:
        """
        Сохранение отчета в файл (.json или .csv).

        Args:
            file_path (str): Путь к файлу для сохранения.
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            if path.suffix.lower() == '.json':
                with path.open('w', encoding='utf-8') as f:
                    f.write(self.to_json())
            elif path.suffix.lower() == '.csv':
                self._save_to_csv(path)
            else:
                logger.warning(f"Неизвестное расширение {path.suffix}, сохраняем как JSON.")
                with path.open('w', encoding='utf-8') as f:
                    f.write(self.to_json())

            logger.info(f"Отчет сохранен: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении отчета в файл {file_path}: {str(e)}")
            raise

    def _save_to_csv(self, path: Path) -> None:
        """
        Сохранение отчета в CSV-файл.

        Args:
            path (Path): Путь к CSV-файлу.
        """
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Entity Type', 'Original Text', 'Replacement', 'Start Position', 'End Position'])

            for item in self.replacements:
                writer.writerow([
                    item.get("entity_type", ""),
                    item.get("original", ""),
                    item.get("replacement", ""),
                    item.get("position", [None, None])[0],
                    item.get("position", [None, None])[1]
                ])
