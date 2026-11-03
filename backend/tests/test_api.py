import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeSeverity:
    def predict(self, texts, projects=None):
        return [
            {"label": "major", "margin": 0.5, "needs_review": False,
             "scores": {"major": 1.0, "normal": 0.5}}
            for _ in texts
        ]


class FakeFinder:
    threshold = 0.8

    def find(self, text, top_k=None, threshold=None):
        return [{"bug_id": 1, "project": "Core", "text": "crash on save", "similarity": 0.9}]


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_models(client):
    client.app.state.severity = FakeSeverity()
    client.app.state.finder = FakeFinder()
    return client


def test_health_without_models(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["models"] == {"severity_loaded": False, "duplicates_loaded": False}


def test_health_with_models(client_with_models):
    body = client_with_models.get("/api/v1/health").json()
    assert body["status"] == "ok"
    assert body["models"] == {"severity_loaded": True, "duplicates_loaded": True}


def test_severity_returns_503_when_model_missing(client):
    response = client.post("/api/v1/severity/predict", json={"text": "app crashes"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == 503


def test_severity_predict_ok(client_with_models):
    response = client_with_models.post(
        "/api/v1/severity/predict", json={"text": "app crashes", "project": "Core"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "major"
    assert "not a probability" in body["note"]


def test_severity_rejects_short_text(client_with_models):
    response = client_with_models.post("/api/v1/severity/predict", json={"text": "a"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == 422


def test_duplicates_returns_503_when_model_missing(client):
    response = client.post("/api/v1/duplicates/search", json={"text": "app crashes"})
    assert response.status_code == 503


def test_duplicates_search_ok(client_with_models):
    response = client_with_models.post(
        "/api/v1/duplicates/search", json={"text": "app crashes", "top_k": 3}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidates"][0]["bug_id"] == 1
    assert body["threshold"] == 0.8
    assert "not a probability" in body["score_type"]


def test_duplicates_rejects_invalid_threshold(client_with_models):
    response = client_with_models.post(
        "/api/v1/duplicates/search", json={"text": "app crashes", "threshold": 1.5}
    )
    assert response.status_code == 422


def test_unknown_route_uses_error_format(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == 404


def test_cors_allows_configured_origin(client):
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    