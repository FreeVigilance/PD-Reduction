import os
import json
import tempfile
import pytest
import sys

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

client = TestClient(app)

@pytest.fixture
def task_with_results():
    """
    Создаёт временную задачу с файлами и сохраняет её в TaskManager.
    """
    task_id = "task-results"
    temp_dir_now = tempfile.mkdtemp(prefix=f"task_{task_id}_")

    original_path = os.path.join(temp_dir_now, "original.txt")
    redacted_path = original_path + ".redacted.txt"
    report_path = original_path + ".report.json"

    with open(original_path, "w", encoding="utf-8") as f:
        f.write("Some original text")

    with open(redacted_path, "w", encoding="utf-8") as f:
        f.write("Some redacted text")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"replacements": []}, f)

    task_manager_now = get_task_manager()
    task_manager_now.save_task(task_id, [original_path])
    task_manager_now.set_status(task_id, "success")
    task_manager_now.update_result(task_id, {
        "original_file": original_path,
        "redacted_file": redacted_path,
        "report_file": report_path
    })

    return task_id

def test_get_results_success(task_with_results):
    """
    Проверяет успешное получение результатов для существующей задачи.
    """
    task_id_now = task_with_results
    response = client.get(f"/results/{task_id_now}")
    assert response.status_code == 200

    result = response.json()
    assert result["task_id"] == task_id_now
    assert len(result["files"]) == 1
    assert len(result["reports"]) == 1
    assert "report" in result["reports"][0]

def test_get_results_not_found():
    """
    Проверка получения 404, если задача не найдена.
    """
    response = client.get("/results/nonexistent-task")
    assert response.status_code == 404
    assert response.json()["detail"] == "Задача не найдена"
