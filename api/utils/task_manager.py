import threading
from typing import Dict, Any, Optional


class TaskManager:
    """
    Менеджер задач. Хранит состояния обработки документов в памяти.

    Каждая задача хранит:
    - список загруженных файлов
    - статус выполнения (pending, processing, success, failed, cancelled)
    - результаты обработки
    - возможную ошибку
    """

    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def save_task(self, task_id: str, files: list[str]) -> None:
        """
        Регистрирует новую задачу.

        Args:
            task_id (str): Уникальный идентификатор задачи.
            files (list[str]): Список путей к исходным файлам.
        """
        with self._lock:
            self._tasks[task_id] = {
                "status": "pending",
                "files": files,
                "results": [],
                "error": None
            }

    def update_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        Добавляет результат обработки к задаче.

        Args:
            task_id (str): ID задачи.
            result (dict): Информация о результате (пути к файлам и отчёт).
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["results"].append(result)

    def set_status(self, task_id: str, status: str, error: Optional[str] = None) -> None:
        """
        Устанавливает статус выполнения задачи.

        Args:
            task_id (str): ID задачи.
            status (str): Статус (pending, processing, success, failed, cancelled).
            error (Optional[str]): Текст ошибки, если задача завершилась с ошибкой.
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status
                if error:
                    self._tasks[task_id]["error"] = error

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить все данные задачи.

        Args:
            task_id (str): ID задачи.

        Returns:
            dict | None: Данные задачи или None, если не найдена.
        """
        with self._lock:
            return self._tasks.get(task_id)

    def task_exists(self, task_id: str) -> bool:
        """
        Проверяет, существует ли задача.

        Args:
            task_id (str): ID задачи.

        Returns:
            bool: True, если задача найдена.
        """
        with self._lock:
            return task_id in self._tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        Помечает задачу как отменённую, если она ещё не завершена.

        Args:
            task_id (str): ID задачи.

        Returns:
            bool: True, если отмена успешна.
        """
        with self._lock:
            if task_id in self._tasks and self._tasks[task_id]["status"] not in ("success", "failed"):
                self._tasks[task_id]["status"] = "cancelled"
                return True
            return False

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Возвращает краткий статус задачи.

        Args:
            task_id (str): ID задачи.

        Returns:
            dict: Статус задачи, количество обработанных и общее число файлов, ошибка если есть.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return {"status": "not_found"}

            return {
                "status": task["status"],
                "files_processed": len(task["results"]),
                "total_files": len(task["files"]),
                "error": task.get("error")
            }

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает список всех задач и их статусов.

        Returns:
            dict: task_id → данные задачи (status, files, results и т.п.)
        """
        with self._lock:
            return dict(self._tasks)
