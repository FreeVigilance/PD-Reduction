from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
import tempfile
import shutil
import os

from api.dependencies import get_engine, get_task_manager
from api.utils.task_manager import TaskManager
from free_vigilance_reduction.core import FreeVigilanceReduction

router = APIRouter()


@router.post("/upload", tags=["Documents"], summary="Загрузка и запуск анонимизации")
def upload_documents(
    files: list[UploadFile] = File(...),
    profile_id: str = Form(...),
    engine: FreeVigilanceReduction = Depends(get_engine),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Загружает один или несколько документов и запускает их обработку (анонимизацию).

    Сохраняет файлы во временную директорию и выполняет обработку каждого файла с использованием заданного профиля.
    Результаты (оригинальный путь, редактированный файл, путь к отчёту) сохраняются в памяти в менеджере задач.

    Args:
        files (list[UploadFile]): Список загружаемых файлов.
        profile_id (str): Идентификатор профиля конфигурации.
        engine (FreeVigilanceReduction): Экземпляр движка анонимизации.
        task_manager (TaskManager): Менеджер задач.

    Returns:
        JSONResponse: Статус задачи, список результатов и task_id.
    """
    task_id = str(uuid4())
    temp_dir = tempfile.mkdtemp(prefix=f"task_{task_id}_")

    saved_paths = []
    results = []

    try:
        for file in files:
            ext = os.path.splitext(file.filename)[-1]
            filename = f"{uuid4()}{ext}"
            file_path = os.path.join(temp_dir, filename)

            with open(file_path, "wb") as out_file:
                shutil.copyfileobj(file.file, out_file)

            saved_paths.append(file_path)

        task_manager.save_task(task_id, saved_paths)
        task_manager.set_status(task_id, "processing")

        for path in saved_paths:
            try:
                report = engine.process_file(path, profile_id=profile_id)

                output_path = path + ".redacted.txt"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report.reduced_text)

                report_path = path + ".report.json"
                report.save_to_file(report_path)

                result_info = {
                    "original_file": path,
                    "redacted_file": output_path,
                    "report_file": report_path,
                }
                results.append(result_info)
                task_manager.update_result(task_id, result_info)

            except Exception as e:
                task_manager.set_status(task_id, "failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

        task_manager.set_status(task_id, "success")

        return JSONResponse(content={
            "task_id": task_id,
            "status": "success",
            "results": results,
        })

    except Exception as e:
        task_manager.set_status(task_id, "failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")
