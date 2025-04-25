# api/tests/test_status.py

import os
import tempfile
import json
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_task_manager
from api.utils.task_manager import TaskManager

client = TestClient(app)

@pytest.fixture
def task_manager_mock():
    """
    Создаёт подмену TaskManager с двумя задачами: завершённой и в процессе.
    """
    manager = TaskManager()

    temp_dir_now = tempfile.mkdtemp()
    redacted_path_now = os.path.join(temp_dir_now, "file.redacted.txt")
    report_path_now = os.path.join(temp_dir_now, "file.report.json")

    with open(redacted_path_now, "w", encoding="utf-8") as redacted_file_now:
        redacted_file_now.write("Заменённый текст")

    with open(report_path_now, "w", encoding="utf-8") as report_file_now:
        json.dump({"entities": []}, report_file_now)

    # Задача "task-ok" — завершена
    manager.save_task("task-ok", ["original.txt"])
    manager.set_status("task-ok", "success")
    manager.update_result("task-ok", {
        "original_file": "original.txt",
        "redacted_file": redacted_path_now,
        "report_file": report_path_now
    })

    # Задача "task-processing" — в процессе
    manager.save_task("task-processing", ["original2.txt"])
    manager.set_status("task-processing", "processing")

    return manager


@pytest.fixture(autouse=True)
def override_dependencies(task_manager_mock):
    """
    Переопределение зависимости get_task_manager на фикстуру.
    """
    app.dependency_overrides[get_task_manager] = lambda: task_manager_mock
    yield
    app.dependency_overrides.clear()


def test_get_status_success():
    """
    Проверяет корректный статус завершённой задачи.
    """
    response = client.get("/status/task-ok")
    assert response.status_code == 200

    data_now = response.json()
    assert data_now["task_id"] == "task-ok"
    assert data_now["status"] == "completed"
    assert data_now["files_processed"] == 1
    assert data_now["total_files"] == 1


def test_get_status_in_progress():
    """
    Проверяет статус задачи, находящейся в процессе.
    """
    response = client.get("/status/task-processing")
    assert response.status_code == 200

    data_now = response.json()
    assert data_now["task_id"] == "task-processing"
    assert data_now["status"] == "in_progress"
    assert data_now["files_processed"] == 0
    assert data_now["total_files"] == 1


def test_get_status_not_found():
    """
    Проверяет поведение при запросе несуществующей задачи.
    """
    response = client.get("/status/task-unknown")
    assert response.status_code == 404
    assert response.json()["detail"] == "Задача не найдена"


def test_get_all_statuses():
    """
    Проверяет получение списка всех задач и их статусов.
    """
    response = client.get("/status")
    assert response.status_code == 200

    data_now = response.json()
    assert "task-ok" in data_now
    assert "task-processing" in data_now

    assert data_now["task-ok"]["status"] == "completed"
    assert data_now["task-processing"]["status"] == "in_progress"

    assert data_now["task-ok"]["progress"] == "1/1"
    assert data_now["task-processing"]["progress"] == "0/1"
