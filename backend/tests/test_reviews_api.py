from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import reviews as reviews_repo

REVIEW = {
    "id": "fb_pred_1",
    "prediction_id": "pred_1",
    "report_id": "br_abc",
    "action": "confirm",
    "predicted_label": "major",
    "final_label": "major",
    "note": None,
    "created_at": datetime(2026, 10, 31, tzinfo=timezone.utc),
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


def test_review_returns_503_without_database(client):
    response = client.post("/api/v1/predictions/pred_1/review", json={"action": "confirm"})
    assert response.status_code == 503


def test_review_missing_prediction_returns_404(api, monkeypatch):
    async def fake_submit(db, prediction_id, action, label, note=None):
        return "not_found", None

    monkeypatch.setattr(reviews_repo, "submit_review", fake_submit)
    response = api.post("/api/v1/predictions/pred_x/review", json={"action": "confirm"})
    assert response.status_code == 404


def test_review_ok_returns_201(api, monkeypatch):
    seen = {}

    async def fake_submit(db, prediction_id, action, label, note=None):
        seen.update(prediction_id=prediction_id, action=action, label=label)
        return "ok", REVIEW

    monkeypatch.setattr(reviews_repo, "submit_review", fake_submit)
    response = api.post("/api/v1/predictions/pred_1/review", json={"action": "confirm"})
    assert response.status_code == 201
    assert response.json()["final_label"] == "major"
    assert seen == {"prediction_id": "pred_1", "action": "confirm", "label": None}


def test_review_twice_returns_409(api, monkeypatch):
    async def fake_submit(db, prediction_id, action, label, note=None):
        return "exists", None

    monkeypatch.setattr(reviews_repo, "submit_review", fake_submit)
    response = api.post("/api/v1/predictions/pred_1/review", json={"action": "confirm"})
    assert response.status_code == 409


def test_correct_without_label_returns_422(api):
    response = api.post("/api/v1/predictions/pred_1/review", json={"action": "correct"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == 422


def test_invalid_label_returns_422(api):
    response = api.post(
        "/api/v1/predictions/pred_1/review", json={"action": "correct", "label": "urgent"}
    )
    assert response.status_code == 422


def test_get_review_missing_returns_404(api, monkeypatch):
    async def fake_get(db, prediction_id):
        return None

    monkeypatch.setattr(reviews_repo, "get_review", fake_get)
    assert api.get("/api/v1/predictions/pred_1/review").status_code == 404


def test_get_review_returns_review(api, monkeypatch):
    async def fake_get(db, prediction_id):
        return REVIEW

    monkeypatch.setattr(reviews_repo, "get_review", fake_get)
    response = api.get("/api/v1/predictions/pred_1/review")
    assert response.status_code == 200
    assert response.json()["prediction_id"] == "pred_1"