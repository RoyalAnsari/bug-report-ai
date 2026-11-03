import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import bug_reports as reports_repo

GOOD = (
    b"Issue ID,Summary,Severity,Product\n"
    b"1,Crash on save,major,Core\n"
    b"2,Typo in menu,minor,JDT\n"
    b"3,x,major,Core\n"
)


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client):
    client.app.state.db = object()  # asli database nahi, upsert fake hoga
    return client


def upload(client, path, data=GOOD, filename="bugs.csv", mapping_raw=None):
    form = {"mapping": mapping_raw} if mapping_raw is not None else None
    return client.post(path, files={"file": (filename, data, "text/csv")}, data=form)


def test_preview_ok(client):
    response = upload(client, "/api/v1/uploads/preview")
    assert response.status_code == 200
    body = response.json()
    assert body["headers"] == ["Issue ID", "Summary", "Severity", "Product"]
    assert body["mapping"]["text"] == "Summary"
    assert body["needs_mapping"] is False
    assert (body["total_rows"], body["valid_rows"], body["error_count"]) == (3, 2, 1)
    assert body["errors"][0]["row"] == 3
    assert len(body["preview"]) == 3
    assert "valid" not in body


def test_preview_asks_for_mapping_when_text_column_unknown(client):
    response = upload(client, "/api/v1/uploads/preview", data=b"A,B\n1,2\n")
    body = response.json()
    assert response.status_code == 200
    assert body["needs_mapping"] is True
    assert body["headers"] == ["A", "B"]
    assert body["valid_rows"] == 0


def test_preview_with_explicit_mapping(client):
    mapping = json.dumps({"text": "A", "severity": "B"})
    response = upload(
        client, "/api/v1/uploads/preview", data=b"A,B\nsome crash text,major\n", mapping_raw=mapping
    )
    body = response.json()
    assert response.status_code == 200
    assert body["needs_mapping"] is False
    assert body["valid_rows"] == 1


def test_preview_rejects_non_csv(client):
    response = upload(client, "/api/v1/uploads/preview", filename="bugs.xlsx")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == 400


def test_preview_rejects_invalid_mapping_json(client):
    response = upload(client, "/api/v1/uploads/preview", mapping_raw="not json")
    assert response.status_code == 400


def test_preview_rejects_unknown_mapping_field(client):
    response = upload(client, "/api/v1/uploads/preview", mapping_raw=json.dumps({"colour": "A"}))
    assert response.status_code == 400


def test_preview_rejects_mapping_column_missing_in_file(client):
    response = upload(client, "/api/v1/uploads/preview", mapping_raw=json.dumps({"text": "Nope"}))
    assert response.status_code == 400


def test_import_returns_503_without_database(client):
    assert upload(client, "/api/v1/uploads/import").status_code == 503


def test_import_ok(api, monkeypatch):
    seen = {}

    async def fake_upsert(db, reports, source, **kwargs):
        seen["reports"] = reports
        seen["source"] = source
        return {"inserted": 1, "already_existed": 1}

    monkeypatch.setattr(reports_repo, "upsert_reports", fake_upsert)
    response = upload(api, "/api/v1/uploads/import")
    assert response.status_code == 200
    body = response.json()
    assert (body["total_rows"], body["valid_rows"], body["error_count"]) == (3, 2, 1)
    assert (body["inserted"], body["already_existed"], body["merged_duplicates"]) == (1, 1, 0)
    assert len(seen["reports"]) == 2
    assert seen["source"] == "csv:bugs.csv"


def test_import_rejects_file_without_valid_rows(api, monkeypatch):
    called = {"value": False}

    async def fake_upsert(db, reports, source, **kwargs):
        called["value"] = True
        return {"inserted": 0, "already_existed": 0}

    monkeypatch.setattr(reports_repo, "upsert_reports", fake_upsert)
    response = upload(api, "/api/v1/uploads/import", data=b"Summary\nx\n")
    assert response.status_code == 400
    assert called["value"] is False


def test_import_requires_text_column(api):
    response = upload(api, "/api/v1/uploads/import", data=b"A,B\n1,2\n")
    assert response.status_code == 400


def test_upload_without_file_returns_422(client):
    assert client.post("/api/v1/uploads/preview").status_code == 422