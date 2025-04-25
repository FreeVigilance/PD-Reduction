"""
Модуль для настройки логирования в системе анонимизации.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


def get_logger(name: str, log_level: Optional[int] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Создание и настройка логгера.

    Args:
        name (str): Имя логгера.
        log_level (int, optional): Уровень логирования. По умолчанию INFO.
        log_file (str, optional): Путь к файлу лога. Если None — логгирование только в консоль.

    Returns:
        logging.Logger: Настроенный логгер.
    """
    if log_level is None:
        log_level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def setup_default_logging(log_dir: Optional[str] = None) -> logging.Logger:
    """
    Настройка логирования по умолчанию.

    Args:
        log_dir (str, optional): Директория для хранения логов. По умолчанию используется 'logs'.

    Returns:
        logging.Logger: Настроенный логгер.
    """
    if log_dir is None:
        log_dir = "logs"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"free_vigilance_reduction_{timestamp}.log")

    return get_logger("free_vigilance_reduction", log_file=log_file)
