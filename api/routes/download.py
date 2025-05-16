from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

import os
import tempfile
from zipfile import ZipFile

router = APIRouter()

@router.get("/download/{task_id}", summary="Скачать архив результатов", tags=["Tasks"])
def download_results(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Сформировать zip-архив с результатами задачи и вернуть его.

    Args:
        task_id (str): Идентификатор задачи.

    Returns:
        FileResponse: Архив с оригиналами, редактированными файлами и отчётами
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task["status"] != "success":
        raise HTTPException(status_code=400, detail="Задача не завершена успешно")

    results = task.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="Нет файлов для скачивания")

    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, f"results_{task_id}.zip")

    with ZipFile(archive_path, "w") as archive:
        for idx, item in enumerate(results, start=1):
            orig_path = item.get("original_file")
            if orig_path and os.path.exists(orig_path):
                ext = os.path.splitext(orig_path)[1] or ".txt"
                arcname = f"original{idx}{ext}"
                archive.write(orig_path, arcname=arcname)

            red_path = item.get("redacted_file")
            if red_path and os.path.exists(red_path):
                ext = os.path.splitext(red_path)[1] or ".txt"
                arcname = f"redacted{idx}{ext}"
                archive.write(red_path, arcname=arcname)

            rep_path = item.get("report_file")
            if rep_path and os.path.exists(rep_path):
                arcname = f"report{idx}.json"
                archive.write(rep_path, arcname=arcname)

    return FileResponse(
        archive_path,
        filename=f"results_{task_id}.zip",
        media_type="application/zip"
    )
