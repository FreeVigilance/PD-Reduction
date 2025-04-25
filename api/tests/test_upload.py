# api/tests/test_upload.py

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_engine, get_task_manager
from free_vigilance_reduction.core import FreeVigilanceReduction
from free_vigilance_reduction.config.configuration import ConfigurationProfile
from api.utils.task_manager import TaskManager

import tempfile
import os


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_upload_environment(monkeypatch):
    """
    Фикстура для настройки движка и менеджера задач.
    """
    engine = get_engine()
    task_manager = get_task_manager()

    test_profile = ConfigurationProfile(
        profile_id="upload_profile",
        entity_types=["PER"],
        replacement_rules={"PER": "template"},
        use_regex=True,
        use_dictionary=False,
        use_language_model=False,
    )

    engine.config_manager.add_profile(test_profile)

    def fake_engine():
        return engine

    def fake_task_manager():
        return task_manager

    monkeypatch.setattr("api.routes.upload.get_engine", fake_engine)
    monkeypatch.setattr("api.routes.upload.get_task_manager", fake_task_manager)
    yield


def test_upload_text_file_success():
    """
    Проверка успешной загрузки текстового файла и запуска анонимизации.
    """
    text_now = "Иван Иванович работает в больнице."
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w+", encoding="utf-8") as temp_file:
        temp_file.write(text_now)
        temp_file_path = temp_file.name

    with open(temp_file_path, "rb") as f:
        response = client.post(
            "/upload",
            data={"profile_id": "upload_profile"},
            files={"files": ("test.txt", f, "text/plain")}
        )

    os.unlink(temp_file_path)

    assert response.status_code == 200
    json_data = response.json()

    assert "task_id" in json_data
    assert json_data["status"] == "success"
    assert isinstance(json_data["results"], list)
    assert len(json_data["results"]) == 1

    result_now = json_data["results"][0]
    assert result_now["original_file"].endswith(".txt")
    assert result_now["redacted_file"].endswith(".redacted.txt")
    assert result_now["report_file"].endswith(".report.json")


def test_upload_invalid_profile():
    """
    Проверка ошибки при загрузке файла с несуществующим профилем.
    """
    text_now = "Тестовый текст."
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w+", encoding="utf-8") as temp_file:
        temp_file.write(text_now)
        temp_file_path = temp_file.name

    with open(temp_file_path, "rb") as f:
        response = client.post(
            "/upload",
            data={"profile_id": "nonexistent_profile"},
            files={"files": ("test.txt", f, "text/plain")}
        )

    os.unlink(temp_file_path)

    assert response.status_code == 500
    assert "Ошибка обработки" in response.text
