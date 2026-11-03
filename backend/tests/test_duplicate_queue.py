import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import duplicate_queue as queue_repo
from app.repositories.duplicate_queue import build_queue_pipeline, to_queue_item


def test_pipeline_filters_by_status_and_pages():
    pipeline = build_queue_pipeline("pending", 20, 20)
    assert pipeline[0] == {"$match": {"status": "pending"}}
    assert {"$sort": {"similarity": -1, "_id": 1}} in pipeline
    assert {"$skip": 20} in pipeline
    assert {"$limit": 20} in pipeline
    assert pipeline[-1]["$lookup"]["from"] == "bug_reports"


def test_pipeline_without_status_has_no_match_stage():
    pipeline = build_queue_pipeline(None, 0, 10)
    assert all("$match" not in stage for stage in pipeline)


def make_doc(report):
    return {
        "_id": "dup_1",
        "report_id": "br_1",
        "candidate_id": "200",
        "candidate_text": "Crash when saving",
        "similarity": 0.9,
        "status": "pending",
        "report": report,
    }


def test_queue_item_gets_text_and_project_of_its_report():
    item = to_queue_item(make_doc([{"text": "Crash on save", "project": "Core"}]))
    assert item["id"] == "dup_1"
    assert item["report_text"] == "Crash on save"
    assert item["report_project"] == "Core"


def test_queue_item_without_a_report_has_empty_report_fields():
    item = to_queue_item(make_doc([]))
    assert item["report_text"] is None
    assert item["report_project"] is None


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


ITEM = {
    "id": "dup_1",
    "report_id": "br_1",
    "candidate_id": "200",
    "candidate_text": "Crash when saving",
    "candidate_project": "Core",
    "similarity": 0.9,
    "score_type": "cosine similarity (not a probability)",
    "status": "pending",
    "created_at": None,
    "report_text": "Crash on save",
    "report_project": "Core",
}


def test_queue_returns_503_without_database(client):
    assert client.get("/api/v1/duplicate-suggestions").status_code == 503


def test_queue_passes_arguments_and_counts_pages(client, monkeypatch):
    seen = {}

    async def fake_list(db, status=None, page=1, page_size=20):
        seen.update(status=status, page=page, page_size=page_size)
        return {"items": [ITEM], "total": 25}

    client.app.state.db = object()
    monkeypatch.setattr(queue_repo, "list_queue", fake_list)
    response = client.get("/api/v1/duplicate-suggestions?status=all&page=2&page_size=10")

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["pages"], body["page"]) == (25, 3, 2)
    assert body["items"][0]["report_text"] == "Crash on save"
    assert "not a probability" in body["items"][0]["score_type"]
    assert seen == {"status": None, "page": 2, "page_size": 10}


def test_queue_shows_pending_suggestions_by_default(client, monkeypatch):
    seen = {}

    async def fake_list(db, status=None, page=1, page_size=20):
        seen["status"] = status
        return {"items": [], "total": 0}

    client.app.state.db = object()
    monkeypatch.setattr(queue_repo, "list_queue", fake_list)
    assert client.get("/api/v1/duplicate-suggestions").status_code == 200
    assert seen["status"] == "pending"


def test_queue_rejects_unknown_status_and_big_page_size(client):
    client.app.state.db = object()
    assert client.get("/api/v1/duplicate-suggestions?status=weird").status_code == 422
    assert client.get("/api/v1/duplicate-suggestions?page_size=500").status_code == 422
