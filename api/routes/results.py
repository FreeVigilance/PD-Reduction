from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

import os
import json

router = APIRouter()

@router.get("/results/{task_id}", summary="Получение результатов", tags=["Tasks"])
def get_results(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Получить список обработанных файлов и их отчётов по задаче.

    Args:
        task_id (str): Идентификатор задачи.

    Returns:
        dict: Список файлов и отчётов.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task["status"] != "success":
        raise HTTPException(status_code=400, detail="Задача ещё не завершена успешно")

    results = task.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="Нет результатов по задаче")

    files_info = []
    reports_info = []

    for res in results:
        file_info = {
            "original_file": os.path.basename(res.get("original_file", "")),
            "redacted_file": os.path.basename(res.get("redacted_file", "")),
        }
        report_path = res.get("report_file")
        if report_path and os.path.exists(report_path):
            with open(report_path, encoding="utf-8") as f:
                report_data = json.load(f)
                reports_info.append({
                    "file": os.path.basename(report_path),
                    "report": report_data
                })
        files_info.append(file_info)

    return JSONResponse(content={
        "task_id": task_id,
        "status": task["status"],
        "files": files_info,
        "reports": reports_info
    })
