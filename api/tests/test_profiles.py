import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_engine
from free_vigilance_reduction.core import FreeVigilanceReduction
from free_vigilance_reduction.config.configuration import ConfigurationProfile

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_profiles(monkeypatch):
    """
    Фикстура для настройки движка с одним тестовым профилем.
    """
    engine = get_engine()

    test_profile = ConfigurationProfile(
        profile_id="test_profile",
        entity_types=["PER"],
        replacement_rules={"PER": "template"}
    )
    engine.config_manager.add_profile(test_profile)

    def fake_get_engine():
        return engine

    monkeypatch.setattr("api.routes.profiles.get_engine", fake_get_engine)
    yield


def test_get_profiles_success():
    """
    Проверка успешного получения списка профилей.
    """
    response = client.get("/profiles")
    assert response.status_code == 200

    profiles = response.json()
    assert isinstance(profiles, list)
    assert "test_profile" in profiles


def test_get_profiles_empty(monkeypatch):
    """
    Проверка случая, когда профилей нет.
    """
    engine = get_engine()
    engine.config_manager.profiles.clear()

    def fake_get_engine():
        return engine

    monkeypatch.setattr("api.routes.profiles.get_engine", fake_get_engine)

    response = client.get("/profiles")
    assert response.status_code == 404
    assert response.json()["detail"] == "Нет доступных профилей"
