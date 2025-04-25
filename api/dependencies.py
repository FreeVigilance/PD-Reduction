import os
from functools import lru_cache

from free_vigilance_reduction.core import FreeVigilanceReduction
from api.utils.task_manager import TaskManager

@lru_cache()
def get_engine() -> FreeVigilanceReduction:
    """
    Создаёт и кэширует анонимизатор.
    """
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "config", "profiles.json")
    regex_path = os.path.join(base_dir, "config", "regex_patterns.json")

    return FreeVigilanceReduction(config_path=config_path, regex_path=regex_path)


@lru_cache()
def get_task_manager() -> TaskManager:
    """
    Создаёт и кэширует менеджер задач.
    """
    return TaskManager()
