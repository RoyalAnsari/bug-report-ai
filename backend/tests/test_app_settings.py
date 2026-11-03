from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories import app_settings as settings_repo
from app.services.app_settings import apply_to_state, merge_with_defaults

DEFAULTS = {"review_margin": 0.25, "duplicate_threshold": 0.8, "duplicate_top_k": 5}
NEW_VALUES = {"review_margin": 0.5, "duplicate_threshold": 0.7, "duplicate_top_k": 10}


def test_merge_uses_the_defaults_when_nothing_is_saved():
    assert merge_with_defaults(DEFAULTS, {}) == DEFAULTS


def test_merge_prefers_saved_values_and_ignores_unknown_keys():
    saved = {"_id": "app", "review_margin": 0.5, "unknown": 1}
    assert merge_with_defaults(DEFAULTS, saved) == {**DEFAULTS, "review_margin": 0.5}


def test_merge_ignores_saved_values_that_are_none():
    assert merge_with_defaults(DEFAULTS, {"duplicate_top_k": None}) == DEFAULTS


def test_apply_changes_the_models_that_are_loaded():
    state = SimpleNamespace(
        severity=SimpleNamespace(review_margin=0.25),
        finder=SimpleNamespace(threshold=0.8, top_k=5),
    )
    apply_to_state(state, NEW_VALUES)
    assert state.severity.review_margin == 0.5
    assert (state.finder.threshold, state.finder.top_k) == (0.7, 10)


def test_apply_skips_models_that_are_not_loaded():
    apply_to_state(SimpleNamespace(severity=None, finder=None), NEW_VALUES)


@pytest.fixture
def client():
    app = create_app(Settings(load_models=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api(client, monkeypatch):
    calls = {"saved": None, "cleared": False}

    async def fake_get_saved(db):
        return {}

    async def fake_save(db, values):
        calls["saved"] = values
        return datetime(2026, 11, 2, tzinfo=timezone.utc)

    async def fake_clear(db):
        calls["cleared"] = True

    client.app.state.db = object()  # no real database
    monkeypatch.setattr(settings_repo, "get_saved", fake_get_saved)
    monkeypatch.setattr(settings_repo, "save", fake_save)
    monkeypatch.setattr(settings_repo, "clear", fake_clear)
    client.calls = calls
    return client


def test_settings_return_503_without_database(client):
    assert client.get("/api/v1/settings").status_code == 503
    assert client.put("/api/v1/settings", json=NEW_VALUES).status_code == 503


def test_get_returns_defaults_and_information_about_the_application(api):
    response = api.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["values"] == DEFAULTS
    assert body["defaults"] == DEFAULTS
    assert body["application"]["database"] == "bug_report_ai"
    assert body["application"]["models_loaded"] == {"severity": False, "duplicates": False}
    assert "mongodb" not in response.text.lower().replace("bug_report_ai", "")


def test_put_saves_and_gives_the_values_to_the_loaded_models(api):
    api.app.state.severity = SimpleNamespace(review_margin=0.25)
    api.app.state.finder = SimpleNamespace(threshold=0.8, top_k=5)

    response = api.put("/api/v1/settings", json=NEW_VALUES)

    assert response.status_code == 200
    body = response.json()
    assert body["values"] == NEW_VALUES
    assert body["application"]["models_loaded"] == {"severity": True, "duplicates": True}
    assert api.calls["saved"] == NEW_VALUES
    assert api.app.state.severity.review_margin == 0.5
    assert (api.app.state.finder.threshold, api.app.state.finder.top_k) == (0.7, 10)


def test_put_rejects_values_outside_the_limits(api):
    for bad in (
        {**NEW_VALUES, "review_margin": 9},
        {**NEW_VALUES, "review_margin": -1},
        {**NEW_VALUES, "duplicate_threshold": 1.5},
        {**NEW_VALUES, "duplicate_top_k": 0},
        {**NEW_VALUES, "duplicate_top_k": 2.5},
    ):
        response = api.put("/api/v1/settings", json=bad)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == 422
    assert api.calls["saved"] is None


def test_reset_clears_the_saved_values_and_restores_the_defaults(api):
    api.app.state.severity = SimpleNamespace(review_margin=0.5)
    api.app.state.finder = SimpleNamespace(threshold=0.7, top_k=10)

    response = api.post("/api/v1/settings/reset")

    assert response.status_code == 200
    assert response.json()["values"] == DEFAULTS
    assert api.calls["cleared"] is True
    assert api.app.state.severity.review_margin == 0.25
    assert (api.app.state.finder.threshold, api.app.state.finder.top_k) == (0.8, 5)
