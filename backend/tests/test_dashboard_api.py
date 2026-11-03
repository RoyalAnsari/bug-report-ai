import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import dashboard as dashboard_repo

SUMMARY = {
    "total_reports": 10,
    "severity_distribution": {
        "blocker": 0, "critical": 1, "major": 2, "normal": 5,
        "minor": 1, "trivial": 1, "unlabeled": 0,
    },
    "predictions_total": 3,
    "reports_with_predictions": 2,
    "pending_reviews": 1,
    "duplicate_suggestions": {"pending": 0, "confirmed": 0, "rejected": 0},
    "duplicate_suggestions_total": 0,
}


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


def test_summary_returns_503_without_database(client):
    assert client.get("/api/v1/dashboard/summary").status_code == 503


def test_summary_returns_data(client, monkeypatch):
    async def fake_summary(db):
        return SUMMARY

    client.app.state.db = object()
    monkeypatch.setattr(dashboard_repo, "get_summary", fake_summary)
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_reports"] == 10
    assert body["pending_reviews"] == 1
    assert body["severity_distribution"]["normal"] == 5