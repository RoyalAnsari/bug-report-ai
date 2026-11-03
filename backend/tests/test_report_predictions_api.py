from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import prediction_records as predictions_repo
from app.repositories import report_crud as reports_repo

REPORT = {"id": "br_abc", "text": "Crash on save", "project": "Core"}

PRED_OUT = {
    "id": "pred_1",
    "report_id": "br_abc",
    "label": "major",
    "margin": 0.5,
    "needs_review": False,
    "scores": {"major": 1.0, "normal": 0.5},
    "model_version": "tfidf-linearsvc-v1",
    "created_at": datetime(2026, 10, 30, tzinfo=timezone.utc),
}


class FakeSeverity:
    def predict(self, texts, projects=None):
        return [
            {"label": "major", "margin": 0.5, "needs_review": False,
             "scores": {"major": 1.0, "normal": 0.5}}
            for _ in texts
        ]


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client):
    client.app.state.db = object()  # asli database nahi
    client.app.state.severity = FakeSeverity()
    return client


def test_predict_returns_503_without_database(client):
    assert client.post("/api/v1/reports/br_abc/predict").status_code == 503


def test_predict_returns_503_without_model(client):
    client.app.state.db = object()
    response = client.post("/api/v1/reports/br_abc/predict")
    assert response.status_code == 503
    assert "model" in response.json()["error"]["message"].lower()


def test_predict_missing_report_returns_404(api, monkeypatch):
    async def fake_get(db, report_id):
        return None

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    assert api.post("/api/v1/reports/br_x/predict").status_code == 404


def test_predict_saves_and_returns_prediction(api, monkeypatch):
    captured = {}

    async def fake_get(db, report_id):
        return REPORT

    async def fake_save(db, report_id, result, **kwargs):
        captured["report_id"] = report_id
        captured["result"] = result
        return PRED_OUT

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    monkeypatch.setattr(predictions_repo, "save_prediction", fake_save)
    response = api.post("/api/v1/reports/br_abc/predict")
    assert response.status_code == 201
    body = response.json()
    assert body["label"] == "major"
    assert body["model_version"] == "tfidf-linearsvc-v1"
    assert "not a probability" in body["note"]
    assert captured["report_id"] == "br_abc"
    assert captured["result"]["label"] == "major"


def test_list_missing_report_returns_404(api, monkeypatch):
    async def fake_get(db, report_id):
        return None

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    assert api.get("/api/v1/reports/br_x/predictions").status_code == 404


def test_list_returns_predictions_and_passes_limit(api, monkeypatch):
    seen = {}

    async def fake_get(db, report_id):
        return REPORT

    async def fake_list(db, report_id, limit=20):
        seen["limit"] = limit
        return [PRED_OUT]

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    monkeypatch.setattr(predictions_repo, "list_predictions", fake_list)
    response = api.get("/api/v1/reports/br_abc/predictions?limit=5")
    assert response.status_code == 200
    assert response.json()[0]["id"] == "pred_1"
    assert seen["limit"] == 5


def test_list_rejects_limit_too_large(api):
    assert api.get("/api/v1/reports/br_abc/predictions?limit=500").status_code == 422