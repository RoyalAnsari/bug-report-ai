from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import report_crud as repo

SAMPLE = {
    "id": "br_abc",
    "text": "Crash on save",
    "project": "Core",
    "severity": "major",
    "external_id": "7",
    "source": "test",
    "created_at": datetime(2026, 10, 30, tzinfo=timezone.utc),
    "updated_at": datetime(2026, 10, 30, tzinfo=timezone.utc),
}


@pytest.fixture
def no_db_client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def api():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as client:
        client.app.state.db = object()  # asli database nahi, repository functions fake hain
        yield client


def test_list_returns_503_without_database(no_db_client):
    response = no_db_client.get("/api/v1/reports")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == 503


def test_list_passes_filters_and_computes_pages(api, monkeypatch):
    seen = {}

    async def fake_list(db, **kwargs):
        seen.update(kwargs)
        return {"items": [SAMPLE], "total": 41}

    monkeypatch.setattr(repo, "list_reports", fake_list)
    response = api.get(
        "/api/v1/reports?page=2&page_size=20&severity=major&project=Core"
        "&search=crash&sort_by=project&order=asc"
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["pages"], body["page"]) == (41, 3, 2)
    assert body["items"][0]["id"] == "br_abc"
    assert seen["severity"] == "major"
    assert seen["sort_by"] == "project"
    assert seen["order"] == "asc"
    assert seen["page_size"] == 20


def test_list_rejects_page_size_too_large(api):
    assert api.get("/api/v1/reports?page_size=500").status_code == 422


def test_list_rejects_unknown_severity(api):
    assert api.get("/api/v1/reports?severity=urgent").status_code == 422


def test_create_returns_201(api, monkeypatch):
    async def fake_create(db, data):
        return {**SAMPLE, "text": data["text"]}

    monkeypatch.setattr(repo, "create_report", fake_create)
    response = api.post("/api/v1/reports", json={"text": "Crash on save", "project": "Core"})
    assert response.status_code == 201
    assert response.json()["text"] == "Crash on save"


def test_create_duplicate_returns_409(api, monkeypatch):
    async def fake_create(db, data):
        return None

    monkeypatch.setattr(repo, "create_report", fake_create)
    response = api.post("/api/v1/reports", json={"text": "Crash on save"})
    assert response.status_code == 409


def test_create_rejects_short_text(api):
    assert api.post("/api/v1/reports", json={"text": "a"}).status_code == 422


def test_get_missing_report_returns_404(api, monkeypatch):
    async def fake_get(db, report_id):
        return None

    monkeypatch.setattr(repo, "get_report", fake_get)
    response = api.get("/api/v1/reports/br_missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == 404


def test_get_existing_report(api, monkeypatch):
    async def fake_get(db, report_id):
        return SAMPLE

    monkeypatch.setattr(repo, "get_report", fake_get)
    assert api.get("/api/v1/reports/br_abc").json()["id"] == "br_abc"


def test_patch_updates_severity(api, monkeypatch):
    async def fake_update(db, report_id, severity):
        return {**SAMPLE, "severity": severity}

    monkeypatch.setattr(repo, "update_severity", fake_update)
    response = api.patch("/api/v1/reports/br_abc", json={"severity": "critical"})
    assert response.status_code == 200
    assert response.json()["severity"] == "critical"


def test_patch_rejects_invalid_severity(api):
    assert api.patch("/api/v1/reports/br_abc", json={"severity": "urgent"}).status_code == 422


def test_patch_missing_report_returns_404(api, monkeypatch):
    async def fake_update(db, report_id, severity):
        return None

    monkeypatch.setattr(repo, "update_severity", fake_update)
    assert api.patch("/api/v1/reports/br_x", json={"severity": "major"}).status_code == 404


def test_delete_returns_204(api, monkeypatch):
    async def fake_delete(db, report_id):
        return True

    monkeypatch.setattr(repo, "delete_report", fake_delete)
    assert api.delete("/api/v1/reports/br_abc").status_code == 204


def test_delete_missing_report_returns_404(api, monkeypatch):
    async def fake_delete(db, report_id):
        return False

    monkeypatch.setattr(repo, "delete_report", fake_delete)
    assert api.delete("/api/v1/reports/br_x").status_code == 404