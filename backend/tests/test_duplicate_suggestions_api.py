import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import duplicate_suggestions as suggestions_repo
from app.repositories import report_crud as reports_repo

REPORT = {"id": "br_abc", "text": "Crash on save", "project": "Core", "external_id": "100"}

SUGGESTION = {
    "id": "dup_1",
    "report_id": "br_abc",
    "candidate_id": "200",
    "candidate_text": "Crash when saving",
    "candidate_project": "Core",
    "similarity": 0.9,
    "score_type": "cosine similarity (not a probability)",
    "status": "pending",
    "created_at": None,
}


class FakeFinder:
    threshold = 0.8
    top_k = 2
    last_call = None

    def find(self, text, top_k=None, threshold=None):
        FakeFinder.last_call = (text, top_k, threshold)
        return [
            {"bug_id": 100, "project": "Core", "text": "Crash on save", "similarity": 1.0},
            {"bug_id": 200, "project": "Core", "text": "Crash when saving", "similarity": 0.9},
            {"bug_id": 300, "project": "JDT", "text": "Save fails", "similarity": 0.85},
        ]


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client):
    client.app.state.db = object()  # asli database nahi
    client.app.state.finder = FakeFinder()
    return client


def test_find_returns_503_without_database(client):
    assert client.post("/api/v1/reports/br_abc/duplicates/find").status_code == 503


def test_find_returns_503_without_model(client):
    client.app.state.db = object()
    response = client.post("/api/v1/reports/br_abc/duplicates/find")
    assert response.status_code == 503
    assert "model" in response.json()["error"]["message"].lower()


def test_find_missing_report_returns_404(api, monkeypatch):
    async def fake_get(db, report_id):
        return None

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    assert api.post("/api/v1/reports/br_x/duplicates/find").status_code == 404


def test_find_drops_self_trims_and_saves(api, monkeypatch):
    saved = {}

    async def fake_get(db, report_id):
        return REPORT

    async def fake_save(db, report_id, hits, threshold):
        saved["ids"] = [h["bug_id"] for h in hits]
        saved["threshold"] = threshold
        return {"inserted": 2, "existing": 0}

    async def fake_list(db, report_id, status=None):
        return [SUGGESTION]

    monkeypatch.setattr(reports_repo, "get_report", fake_get)
    monkeypatch.setattr(suggestions_repo, "save_candidates", fake_save)
    monkeypatch.setattr(suggestions_repo, "list_suggestions", fake_list)

    response = api.post("/api/v1/reports/br_abc/duplicates/find", json={"top_k": 2, "threshold": 0.5})
    assert response.status_code == 200
    body = response.json()
    assert saved["ids"] == [200, 300]  # report khud (100) nikal gayi
    assert saved["threshold"] == 0.5
    assert FakeFinder.last_call[1] == 3  # top_k + 1 maanga gaya
    assert (body["found"], body["new"]) == (2, 2)
    assert body["suggestions"][0]["id"] == "dup_1"
    assert "not a probability" in body["suggestions"][0]["score_type"]


def test_list_passes_status_filter(api, monkeypatch):
    seen = {}

    async def fake_list(db, report_id, status=None):
        seen["status"] = status
        return [SUGGESTION]

    monkeypatch.setattr(suggestions_repo, "list_suggestions", fake_list)
    response = api.get("/api/v1/reports/br_abc/duplicates?status=pending")
    assert response.status_code == 200
    assert seen["status"] == "pending"


def test_list_rejects_invalid_status(api):
    assert api.get("/api/v1/reports/br_abc/duplicates?status=weird").status_code == 422


def test_review_ok_returns_201(api, monkeypatch):
    async def fake_review(db, suggestion_id, decision, note=None):
        return "ok", {**SUGGESTION, "status": "confirmed"}

    monkeypatch.setattr(suggestions_repo, "review_suggestion", fake_review)
    response = api.post("/api/v1/duplicate-suggestions/dup_1/review", json={"decision": "confirm"})
    assert response.status_code == 201
    assert response.json()["status"] == "confirmed"


def test_review_twice_returns_409(api, monkeypatch):
    async def fake_review(db, suggestion_id, decision, note=None):
        return "exists", None

    monkeypatch.setattr(suggestions_repo, "review_suggestion", fake_review)
    response = api.post("/api/v1/duplicate-suggestions/dup_1/review", json={"decision": "reject"})
    assert response.status_code == 409


def test_review_missing_returns_404(api, monkeypatch):
    async def fake_review(db, suggestion_id, decision, note=None):
        return "not_found", None

    monkeypatch.setattr(suggestions_repo, "review_suggestion", fake_review)
    response = api.post("/api/v1/duplicate-suggestions/dup_x/review", json={"decision": "confirm"})
    assert response.status_code == 404


def test_review_invalid_decision_returns_422(api):
    response = api.post("/api/v1/duplicate-suggestions/dup_1/review", json={"decision": "maybe"})
    assert response.status_code == 422