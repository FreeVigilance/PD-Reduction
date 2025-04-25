# api/tests/test_download.py

import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from zipfile import ZipFile

from api.main import app
from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

client = TestClient(app)


@pytest.fixture
def temp_files():
    temp_dir = tempfile.mkdtemp()
    original_path = os.path.join(temp_dir, "original.txt")
    redacted_path = os.path.join(temp_dir, "original.txt.redacted.txt")
    report_path = os.path.join(temp_dir, "original.txt.report.json")

    with open(original_path, "w", encoding="utf-8") as f:
        f.write("Ориг")

    with open(redacted_path, "w", encoding="utf-8") as f:
        f.write("Ред")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("{}")

    yield {
        "original_file": original_path,
        "redacted_file": redacted_path,
        "report_file": report_path,
        "temp_dir": temp_dir
    }

    shutil.rmtree(temp_dir)


def test_download_success(temp_files):
    task_id = "test-success"
    task_manager = get_task_manager()
    task_manager.save_task(task_id, [temp_files["original_file"]])
    task_manager.set_status(task_id, "success")
    task_manager.update_result(task_id, {
        "original_file": temp_files["original_file"],
        "redacted_file": temp_files["redacted_file"],
        "report_file": temp_files["report_file"],
    })

    response = client.get(f"/download/{task_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"


def test_download_not_success(temp_files):
    task_id = "test-failed"
    task_manager = get_task_manager()
    task_manager.save_task(task_id, [temp_files["original_file"]])
    task_manager.set_status(task_id, "failed")

    response = client.get(f"/download/{task_id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Задача не завершена успешно"


def test_download_no_results(temp_files):
    task_id = "test-no-results"
    task_manager = get_task_manager()
    task_manager.save_task(task_id, [temp_files["original_file"]])
    task_manager.set_status(task_id, "success")
    response = client.get(f"/download/{task_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Нет файлов для скачивания"


def test_download_task_not_found():
    response = client.get("/download/unknown-task")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Задача не найдена"
