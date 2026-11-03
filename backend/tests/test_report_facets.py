import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import report_crud as reports_repo
from app.repositories import report_facets as facets_repo
from app.repositories.report_facets import clean_projects


def test_clean_projects_removes_empty_values_and_repeats():
    assert clean_projects(["Core", None, "", "  ", "Core", "JDT"]) == ["Core", "JDT"]


def test_clean_projects_sorts_ignoring_capital_letters():
    assert clean_projects(["jdt", "Core", "Platform"]) == ["Core", "jdt", "Platform"]


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


def test_projects_returns_503_without_database(client):
    assert client.get("/api/v1/reports/projects").status_code == 503


def test_projects_route_is_not_taken_by_the_report_id_route(client, monkeypatch):
    async def fake_list(db):
        return ["Core", "JDT"]

    async def fail_get(db, report_id):
        raise AssertionError("get_report must not be called for /reports/projects")

    client.app.state.db = object()
    monkeypatch.setattr(facets_repo, "list_projects", fake_list)
    monkeypatch.setattr(reports_repo, "get_report", fail_get)

    response = client.get("/api/v1/reports/projects")
    assert response.status_code == 200
    assert response.json() == {"projects": ["Core", "JDT"]}
