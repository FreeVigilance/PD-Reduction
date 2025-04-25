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
        FileResponse: Архив с redacted и report файлами.
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
        for item in results:
            for file_type in ("original_file", "redacted_file", "report_file"):
                path = item.get(file_type)
                if path and os.path.exists(path):
                    archive.write(path, arcname=os.path.basename(path))

    return FileResponse(
        archive_path,
        filename=f"results_{task_id}.zip",
        media_type="application/zip"
    )
