"""
Модуль обёртки над языковой моделью для контекстного анализа и поиска сущностей.

Загрузка модели происходит ТОЛЬКО из локального пути, указанного в llm_settings
JSON-профиля. Текст разбивается на токен-чанки в соответствии с настройками
max_input_tokens и chunk_overlap_tokens.
"""

import re
from typing import List, Dict, Any
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import spacy

from ..entity_recognition.entity import Entity
from ..config.configuration import ConfigurationProfile
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LanguageModel:
    """
    Обёртка над LLM (Vikhr-Gemma-2B-instruct) для поиска и разметки сущностей в тексте.

    Методы:
      - search_entities(text, profile)
      - _initialize(llm_settings)
      - _chunk_text(text, max_tokens, overlap)
      - _generate_prompt(text, profile)
    """

    def __init__(self):
        """
        Конструктор инициализирует атрибуты без загрузки модели.
        spaCy загружается сразу.
        """
        self.tokenizer: AutoTokenizer = None
        self.model: AutoModelForCausalLM = None
        self.device: torch.device = None
        self.initialized: bool = False
        try:
            self.nlp = spacy.load("ru_core_news_sm")
        except OSError:
            logger.warning("spaCy модель 'ru_core_news_sm' не найдена, попробуйте установить её через 'python -m spacy download ru_core_news_sm'")
            self.nlp = None

    def _initialize(self, llm_settings: Dict[str, Any]) -> None:
        """
        Локальная загрузка модели и токенизатора по настройкам.

        Args:
            llm_settings (dict): Словарь с настройками:
                - model_path (str): локальный путь к модели
                - device (str): 'cpu' или 'cuda'/'cuda:0'
                - max_input_tokens (int)
                - chunk_overlap_tokens (int)
                - max_new_tokens (int)
                - temperature (float)
        """
        model_path = llm_settings.get("model_path", "")
        if not model_path:
            msg = "LLM: не указан путь 'model_path' в настройках."
            logger.error(msg)
            raise ValueError(msg)

        path = Path(model_path)
        if not path.exists():
            msg = f"LLM: указанный путь до модели не найден: '{model_path}'"
            logger.error(msg)
            raise ValueError(msg)

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            use_fast=True,
            local_files_only=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            local_files_only=True
        )

        device_cfg = llm_settings.get("device", "cpu").lower()
        if device_cfg.startswith("cuda") and torch.cuda.is_available():
            gpu_device = device_cfg if device_cfg.startswith("cuda:") else "cuda:0"
            self.device = torch.device(gpu_device)
        else:
            self.device = torch.device("cpu")
        self.model.to(self.device)

        logger.info(f"LLM загружена на устройство {self.device} из {model_path}")
        self.initialized = True

    def _chunk_text(
        self,
        text: str,
        max_tokens: int,
        overlap: int
    ) -> List[str]:
        """
        Разбивка текста на фрагменты по токенам с указанным перекрытием.

        Args:
            text (str): Исходный текст.
            max_tokens (int): Максимальное число токенов в чанке.
            overlap (int): Число токенов пересечения между чанками.

        Returns:
            List[str]: Список текстовых чанков.
        """
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        total = len(token_ids)
        if total <= max_tokens:
            return [text]

        chunks: List[str] = []
        start = 0
        while start < total:
            end = start + max_tokens
            slice_ids = token_ids[start:end]
            chunk_text = self.tokenizer.decode(
                slice_ids,
                clean_up_tokenization_spaces=True
            )
            chunks.append(chunk_text)
            if end >= total:
                break
            start = end - overlap
        return chunks

    def _generate_prompt(
        self,
        text: str,
        profile: ConfigurationProfile
    ) -> str:
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
        for etype in profile.entity_types:
            desc = profile.custom_entity_prompts.get(etype, f"Тип {etype}")
            lines.append(f"- <{etype}>...</{etype}> — {desc}")
        lines += [
            "",
            "ВАЖНО:",
            "- Используй точные подстроки из текста, не изменяя форму слов.",
            "- Не объединяй разные сущности. Одна сущность - одно или всего пару слов, не больше!",
            "- Не объясняй свои действия. Не добавляй ничего лишнего.",
            "- Одна и та же сущность может быть очень много раз. Найди все!",
            "",
            "Текст для анализа:",
            "",
            text,
            "",
            "Размеченный текст (верни текст для анализа целиком, но с размеченными сущностями):"
        ]
        return "\n".join(lines)

    def search_entities(
        self, text: str, profile: ConfigurationProfile
    ) -> List[Entity]:
        """
        Поиск сущностей в тексте с использованием LLM и chunk tagging.

        Разбивает текст на чанки, формирует для каждого промпт через _generate_prompt,
        генерирует размеченный текст, затем извлекает теги и возвращает объекты Entity.
        При невозможности точного совпадения применяется spaCy для лемматизации и
        нечеткий поиск через RapidFuzz.

        Args:
            text (str): Исходный текст для анализа.
            profile (ConfigurationProfile): Конфигурационный профиль.

        Returns:
            List[Entity]: Список найденных сущностей.
        """
        from rapidfuzz import fuzz
        from .entity_recognizer import EntityRecognizer

        if not profile.use_language_model:
            return []

        if not self.initialized:
            self._initialize(profile.llm_settings)

        max_tok   = profile.llm_settings.get("max_input_tokens", 512)
        overlap   = profile.llm_settings.get("chunk_overlap_tokens", 0)
        max_new   = profile.llm_settings.get("max_new_tokens", 256)
        temp      = profile.llm_settings.get("temperature", 0.5)
        fuzzy_thr = profile.llm_settings.get("fuzzy_threshold", 85) 

        entities: List[Entity] = []

        for chunk in self._chunk_text(text, max_tok, overlap):
            prompt = self._generate_prompt(chunk, profile)
            print(f"LLM prompt:\n{prompt}")
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)
            attn_mask = inputs.get("attention_mask")
            if attn_mask is not None:
                attn_mask = attn_mask.to(self.device)

            with torch.no_grad():
                out_ids = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attn_mask,
                    max_new_tokens=max_new,
                    temperature=temp,
                    do_sample=True
                )
            tagged = self.tokenizer.decode(out_ids[0], skip_special_tokens=True).strip()
            print(f"LLM raw output:\n{tagged}")

            for et in profile.entity_types:
                pattern = re.compile(f"<{et}>(.+?)</{et}>")
                for m in pattern.finditer(tagged):
                    ent_text = m.group(1)
                    matched = False

                    for mm in re.finditer(re.escape(ent_text), text):
                        entities.append(Entity(ent_text, et, *mm.span()))
                        matched = True

                    if not matched and self.nlp:
                        ent_doc = self.nlp(ent_text)
                        if ent_doc:
                            lemma = ent_doc[0].lemma_
                            for tok in self.nlp(text):
                                if tok.lemma_ == lemma:
                                    entities.append(
                                        Entity(tok.text, et, tok.idx, tok.idx + len(tok.text))
                                    )
                                    matched = True
                                    break

                    if not matched:
                        L0 = len(ent_text)
                        delta = max(1, int(0.2 * L0))
                        for L in (L0 - delta, L0 + delta):
                            if L < 1:
                                continue
                            for i in range(0, len(text) - L + 1):
                                candidate = text[i : i + L]
                                score = fuzz.ratio(ent_text.lower(), candidate.lower())
                                if score >= fuzzy_thr:
                                    entities.append(Entity(candidate, et, i, i + len(candidate)))
                                    matched = True
                                    break
                            if matched:
                                break

        return EntityRecognizer()._deduplicate_entities(entities)
