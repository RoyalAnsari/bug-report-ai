from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_client(**options):
    return TestClient(create_app(Settings(load_models=False, **options)))


def test_api_responses_have_security_headers():
    with make_client() as client:
        response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert "strict-transport-security" not in response.headers


def test_error_responses_also_have_security_headers():
    with make_client() as client:
        response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"


def test_hsts_is_sent_only_when_enabled():
    with make_client(enable_hsts=True) as client:
        response = client.get("/api/v1/health")
    assert "max-age" in response.headers["strict-transport-security"]


def test_docs_are_off_by_default():
    with make_client() as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_docs_work_when_enabled_and_are_not_blocked_by_the_api_csp():
    with make_client(enable_docs=True) as client:
        response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


def test_lockout_settings_are_checked_at_startup():
    import pytest

    with pytest.raises(ValueError):
        create_app(Settings(load_models=False, max_failed_logins=0))
