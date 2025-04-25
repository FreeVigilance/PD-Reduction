"""
Роуты для получения статуса задач анонимизации.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict
import os

from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

router = APIRouter()


@router.get("/status/{task_id}", summary="Статус задачи", tags=["Tasks"])
def get_task_status(task_id: str, task_manager: TaskManager = Depends(get_task_manager)):
    """
    Возвращает статус обработки конкретной задачи по её `task_id`.

    Args:
        task_id (str): Уникальный идентификатор задачи.

    Returns:
        JSONResponse: Статус, число обработанных файлов и общее число.
    """
    task_now = task_manager.get_task(task_id)
    if not task_now:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    results_now = task_now.get("results", [])
    total_files_now = len(task_now.get("files", []))

    completed_now = 0
    for result_now in results_now:
        report_path_now = result_now.get("report_file", "")
        redacted_path_now = result_now.get("redacted_file", "")
        if os.path.exists(report_path_now) and os.path.exists(redacted_path_now):
            completed_now += 1

    if completed_now == total_files_now:
        status_now = "completed"
    elif completed_now > 0:
        status_now = "partial"
    else:
        status_now = "in_progress"

    return JSONResponse(content={
        "task_id": task_id,
        "status": status_now,
        "files_processed": completed_now,
        "total_files": total_files_now,
        "error": task_now.get("error")
    })


@router.get("/status", summary="Список всех задач", tags=["Tasks"])
def list_all_tasks(task_manager: TaskManager = Depends(get_task_manager)) -> Dict[str, Dict[str, str]]:
    """
    Возвращает список всех задач с их статусами и прогрессом.

    Returns:
        Dict[str, Dict[str, str]]: Словарь формата {task_id: {"status": str, "progress": str}}.
    """
    all_tasks_now = task_manager.get_all_tasks()
    result_now = {}

    for task_id_now, task_now in all_tasks_now.items():
        results_now = task_now.get("results", [])
        total_files_now = len(task_now.get("files", []))

        completed_now = 0
        for result_now_item in results_now:
            report_path_now = result_now_item.get("report_file", "")
            redacted_path_now = result_now_item.get("redacted_file", "")
            if os.path.exists(report_path_now) and os.path.exists(redacted_path_now):
                completed_now += 1

        if completed_now == total_files_now:
            status_now = "completed"
        elif completed_now > 0:
            status_now = "partial"
        else:
            status_now = "in_progress"

        progress_now = f"{completed_now}/{total_files_now}"
        result_now[task_id_now] = {
            "status": status_now,
            "progress": progress_now
        }

    return result_now
