from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.repositories.reviews import build_feedback_document, resolve_final_label
from app.schemas.reviews import ReviewRequest

PREDICTION = {"_id": "pred_1", "report_id": "br_abc", "label": "major"}


def test_confirm_uses_predicted_label():
    assert resolve_final_label("major", "confirm", None) == "major"


def test_correct_uses_given_label():
    assert resolve_final_label("major", "correct", "critical") == "critical"


def test_feedback_document_fields():
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    doc = build_feedback_document(PREDICTION, "correct", "critical", "looks worse", now)
    assert doc["target_type"] == "prediction"
    assert doc["target_id"] == "pred_1"
    assert doc["report_id"] == "br_abc"
    assert doc["predicted_label"] == "major"
    assert doc["final_label"] == "critical"
    assert doc["note"] == "looks worse"
    assert doc["created_at"] == now


def test_feedback_id_is_tied_to_prediction():
    first = build_feedback_document(PREDICTION, "confirm", "major")
    second = build_feedback_document(PREDICTION, "confirm", "major")
    assert first["_id"] == second["_id"] == "fb_pred_1"


def test_request_correct_requires_label():
    with pytest.raises(ValidationError):
        ReviewRequest(action="correct")


def test_request_confirm_rejects_label():
    with pytest.raises(ValidationError):
        ReviewRequest(action="confirm", label="major")


def test_request_valid_cases():
    assert ReviewRequest(action="confirm").label is None
    assert ReviewRequest(action="correct", label="minor", note="  ok  ").note == "ok"