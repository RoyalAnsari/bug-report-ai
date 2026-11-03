import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import model_versions as versions_repo

SUMMARY = {
    "id": "severity-classifier:v1",
    "name": "severity-classifier",
    "version": "v1",
    "task": "severity classification",
    "has_evaluation": True,
    "macro_f1": 0.6,
    "created_at": None,
}

DETAIL = {
    "id": "severity-classifier:v1",
    "name": "severity-classifier",
    "version": "v1",
    "task": "severity classification",
    "algorithm": "TF-IDF + LinearSVC",
    "evaluation": {"macro_f1": 0.6, "confusion_matrix": [[1, 0], [0, 1]]},
}


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client):
    client.app.state.db = object()  # asli database nahi
    return client


def test_list_returns_503_without_database(client):
    assert client.get("/api/v1/models").status_code == 503


def test_list_returns_models(api, monkeypatch):
    async def fake_list(db):
        return [SUMMARY]

    monkeypatch.setattr(versions_repo, "list_versions", fake_list)
    response = api.get("/api/v1/models")
    assert response.status_code == 200
    assert response.json()[0]["macro_f1"] == 0.6


def test_detail_missing_returns_404(api, monkeypatch):
    async def fake_get(db, name, version):
        return None

    monkeypatch.setattr(versions_repo, "get_version", fake_get)
    assert api.get("/api/v1/models/nope/v9").status_code == 404


def test_detail_returns_model(api, monkeypatch):
    seen = {}

    async def fake_get(db, name, version):
        seen["args"] = (name, version)
        return DETAIL

    monkeypatch.setattr(versions_repo, "get_version", fake_get)
    response = api.get("/api/v1/models/severity-classifier/v1")
    assert response.status_code == 200
    assert response.json()["evaluation"]["confusion_matrix"] == [[1, 0], [0, 1]]
    assert seen["args"] == ("severity-classifier", "v1")