"""
Модуль для взаимодействия с языковой моделью (LLM) для выявления сущностей.
"""

import re
from typing import List
from transformers import AutoTokenizer, AutoModelForCausalLM
from ..config.configuration import ConfigurationProfile
from ..entity_recognition.entity import Entity
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LanguageModel:
    """
    Класс для взаимодействия с языковой моделью (LLM) и извлечения сущностей из текста.
    """

    def __init__(self, model_name: str = "Vikhrmodels/Vikhr-Gemma-2B-instruct"):
        """
        Инициализация языковой модели и токенизатора.

        Args:
            model_name (str): Имя модели HuggingFace.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def _generate_prompt(self, text: str, profile: ConfigurationProfile) -> str:
        """
        Формирование промпта для генерации в формате chunk tagging.

        Args:
            text (str): Текст для анализа.
            profile (ConfigurationProfile): Настройки профиля.

        Returns:
            str: Готовый промпт для подачи в модель.
        """
        lines = [
            "Ты — алгоритм для анонимизации текста. Обозначь в тексте персональные данные, обернув их в соответствующие теги.",
            "",
            "Типы тегов, которые нужно использовать:"
        ]

        for entity_type in profile.entity_types:
            description = profile.custom_entity_prompts.get(entity_type, f"Тип {entity_type}")
            lines.append(f"- <{entity_type}>...</{entity_type}> — {description}")

        lines += [
            "",
            "ВАЖНО:",
            "- Используй точные подстроки из текста, не изменяя форму слов.",
            "- Не объединяй разные сущности.",
            "- Не объясняй свои действия. Не добавляй ничего лишнего.",
            "- Одна и та же сущность может быть очень много раз. Найди все!",
            "",
            "Текст для анализа (верни текст целиком, но с размеченными сущностями):",
            "",
            text,
            "",
            "Ответ:"
        ]

        return "\n".join(lines)

    def _chunk_text(self, text: str, max_input_tokens: int, chunk_overlap_tokens: int) -> List[str]:
        """
        Разбиение текста на чанки по количеству токенов с перекрытием.

        Args:
            text (str): Полный текст.
            max_input_tokens (int): Максимальное число токенов.
            chunk_overlap_tokens (int): Количество перекрывающихся токенов между чанками.

        Returns:
            List[str]: Список чанков.
        """
        input_ids = self.tokenizer.encode(text, add_special_tokens=False)
        chunk_size = max_input_tokens - 400
        chunks = []
        start = 0

        while start < len(input_ids):
            end = min(start + chunk_size, len(input_ids))
            chunk_ids = input_ids[start:end]
            chunk_text = self.tokenizer.decode(chunk_ids)
            chunks.append(chunk_text)
            start = end - chunk_overlap_tokens
            if start <= 0:
                start = end

        return chunks

    def search_entities(self, text: str, profile: ConfigurationProfile) -> List[Entity]:
        """
        Поиск сущностей в тексте с помощью языковой модели.

        Args:
            text (str): Текст для анализа.
            profile (ConfigurationProfile): Профиль настроек.

        Returns:
            List[Entity]: Найденные сущности.
        """
        settings = profile.llm_settings or {}
        max_input_tokens = settings.get("max_input_tokens", 4000)
        chunk_overlap_tokens = settings.get("chunk_overlap_tokens", 200)
        max_new_tokens = settings.get("max_new_tokens", 200)
        temperature = settings.get("temperature", 0.8)

        entities: List[Entity] = []
        chunks = self._chunk_text(text, max_input_tokens, chunk_overlap_tokens)

        for chunk in chunks:
            try:
                prompt = self._generate_prompt(chunk, profile)
                print("\n[DEBUG PROMPT]")
                print(prompt)
                input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids

                output = self.model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=1.0,
                    top_k=5,
                    do_sample=False,
                    eos_token_id=self.tokenizer.eos_token_id
                )

                result = self.tokenizer.decode(output[0], skip_special_tokens=True)
                print("\n[DEBUG RAW OUTPUT]")
                print(result)
                extracted = self._extract_entities(result, chunk, profile)
                entities.extend(extracted)

            except Exception as e:
                logger.error(f"Ошибка генерации на чанке: {e}")

        return entities

    def _extract_entities(self, generated_text: str, original_text: str, profile: ConfigurationProfile) -> List[Entity]:
        """
        Извлечение сущностей из сгенерированного текста.

        Args:
            generated_text (str): Ответ модели.
            original_text (str): Оригинальный чанк.
            profile (ConfigurationProfile): Профиль настроек.

        Returns:
            List[Entity]: Найденные сущности.
        """
        found = []
        for entity_type in profile.entity_types:
            open_tag = f"<{entity_type}>"
            close_tag = f"</{entity_type}>"
            start = 0

            while True:
                open_pos = generated_text.find(open_tag, start)
                close_pos = generated_text.find(close_tag, open_pos)
                if open_pos == -1 or close_pos == -1:
                    break

                entity_text = generated_text[open_pos + len(open_tag):close_pos].strip()
                if not entity_text:
                    start = close_pos + len(close_tag)
                    continue

                original_start = original_text.find(entity_text)
                if original_start == -1:
                    start = close_pos + len(close_tag)
                    continue

                original_end = original_start + len(entity_text)
                found.append(Entity(entity_text, entity_type, original_start, original_end))
                start = close_pos + len(close_tag)

        return found
