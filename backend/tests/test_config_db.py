import pytest

from app.core.config import Settings
from app.db.mongo import create_client


def test_settings_reads_mongodb_values(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB", "test_db")
    settings = Settings.from_env()
    assert settings.mongodb_uri == "mongodb://localhost:27017"
    assert settings.mongodb_db == "test_db"


def test_settings_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("MONGODB_DB", raising=False)
    settings = Settings.from_env()
    assert settings.mongodb_uri == ""
    assert settings.mongodb_db == "bug_report_ai"


def test_settings_repr_hides_connection_string():
    settings = Settings(mongodb_uri="mongodb+srv://user:secret@host")
    assert "secret" not in repr(settings)


def test_create_client_rejects_empty_uri():
    with pytest.raises(ValueError):
        create_client("")