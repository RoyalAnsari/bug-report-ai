from datetime import datetime, timezone

from app.repositories.prediction_records import (
    SEVERITY_MODEL_VERSION,
    build_prediction_document,
    to_out,
)

RESULT = {
    "label": "major",
    "margin": 0.5,
    "needs_review": True,
    "scores": {"major": 1.0, "normal": 0.5},
}


def test_document_has_expected_fields():
    now = datetime(2026, 10, 30, tzinfo=timezone.utc)
    doc = build_prediction_document("br_abc", RESULT, now=now)
    assert doc["_id"].startswith("pred_")
    assert doc["report_id"] == "br_abc"
    assert doc["label"] == "major"
    assert doc["margin"] == 0.5
    assert doc["needs_review"] is True
    assert doc["scores"] == RESULT["scores"]
    assert doc["model_version"] == SEVERITY_MODEL_VERSION
    assert doc["created_at"] == now


def test_each_prediction_gets_its_own_id():
    first = build_prediction_document("br_abc", RESULT)
    second = build_prediction_document("br_abc", RESULT)
    assert first["_id"] != second["_id"]


def test_to_out_maps_id_and_keeps_values():
    doc = build_prediction_document("br_abc", RESULT)
    out = to_out(doc)
    assert out["id"] == doc["_id"]
    assert out["report_id"] == "br_abc"
    assert out["needs_review"] is True


def test_created_at_is_set_automatically():
    doc = build_prediction_document("br_abc", RESULT)
    assert doc["created_at"].tzinfo is not None