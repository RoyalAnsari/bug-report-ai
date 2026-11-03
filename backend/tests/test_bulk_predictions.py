import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import bulk_predictions as bulk_repo
from app.services.bulk_predict import chunks, predict_in_batches

REPORTS = [
    {"id": "br_1", "text": "Crash on save", "project": "Core"},
    {"id": "br_2", "text": "Typo in menu", "project": "JDT"},
    {"id": "br_3", "text": "Data loss on exit", "project": "Core"},
]


class FakePredictor:
    def __init__(self):
        self.calls = []

    def predict(self, texts, projects=None):
        self.calls.append(list(texts))
        return [
            {
                "label": "major",
                "margin": 0.1 if "Crash" in text or "loss" in text else 0.9,
                "needs_review": "Crash" in text or "loss" in text,
                "scores": {"major": 1.0, "normal": 0.5},
            }
            for text in texts
        ]


def test_chunks_cuts_the_list_into_pieces():
    assert list(chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_chunks_rejects_a_size_below_one():
    with pytest.raises(ValueError):
        list(chunks([1], 0))


def test_predict_in_batches_keeps_the_order_and_uses_pieces():
    predictor = FakePredictor()
    pairs = predict_in_batches(predictor, REPORTS, batch_size=2)

    assert [report_id for report_id, _ in pairs] == ["br_1", "br_2", "br_3"]
    assert [len(call) for call in predictor.calls] == [2, 1]
    assert pairs[1][1]["needs_review"] is False


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client, monkeypatch):
    calls = {"saved": None}

    async def fake_find(db, limit):
        calls["limit"] = limit
        return list(REPORTS)

    async def fake_save(db, documents):
        calls["saved"] = documents

    async def fake_count(db):
        return {"total_reports": 3, "reports_with_predictions": 3, "unpredicted": 0}

    client.app.state.db = object()  # no real database
    client.app.state.severity = FakePredictor()
    monkeypatch.setattr(bulk_repo, "find_unpredicted", fake_find)
    monkeypatch.setattr(bulk_repo, "save_many", fake_save)
    monkeypatch.setattr(bulk_repo, "count_unpredicted", fake_count)
    client.calls = calls
    return client


def test_status_returns_the_counts(api):
    response = api.get("/api/v1/predictions/bulk/status")
    assert response.status_code == 200
    assert response.json() == {"total_reports": 3, "reports_with_predictions": 3, "unpredicted": 0}


def test_bulk_returns_503_without_a_database(client):
    assert client.post("/api/v1/predictions/bulk", json={}).status_code == 503


def test_bulk_returns_503_when_the_model_is_not_loaded(api):
    api.app.state.severity = None
    response = api.post("/api/v1/predictions/bulk", json={})
    assert response.status_code == 503
    assert "not loaded" in response.json()["error"]["message"]


def test_bulk_predicts_and_saves_every_report(api):
    response = api.post("/api/v1/predictions/bulk", json={"limit": 50})

    assert response.status_code == 200
    body = response.json()
    assert (body["requested"], body["predicted"], body["needs_review"], body["remaining"]) == (3, 3, 2, 0)
    assert body["model_version"] == "tfidf-linearsvc-v1"
    assert "not a probability" in body["note"]
    assert api.calls["limit"] == 50
    saved = api.calls["saved"]
    assert [d["report_id"] for d in saved] == ["br_1", "br_2", "br_3"]
    assert all(d["_id"].startswith("pred_") for d in saved)


def test_bulk_with_nothing_to_predict_saves_nothing(api, monkeypatch):
    async def fake_find(db, limit):
        return []

    monkeypatch.setattr(bulk_repo, "find_unpredicted", fake_find)
    response = api.post("/api/v1/predictions/bulk", json={})

    assert response.status_code == 200
    assert response.json()["predicted"] == 0
    assert api.calls["saved"] is None


def test_bulk_rejects_a_limit_outside_1_to_500(api):
    assert api.post("/api/v1/predictions/bulk", json={"limit": 0}).status_code == 422
    assert api.post("/api/v1/predictions/bulk", json={"limit": 501}).status_code == 422
