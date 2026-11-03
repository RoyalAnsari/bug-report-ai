from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.repositories.duplicate_suggestions import (
    build_suggestion_fields,
    drop_self_matches,
    make_suggestion_id,
    to_out,
)
from app.schemas.duplicate_suggestions import SuggestionReviewRequest

HITS = [
    {"bug_id": 100, "project": "Core", "text": "same report", "similarity": 1.0},
    {"bug_id": 200, "project": "Core", "text": "other report", "similarity": 0.9},
]


def test_suggestion_id_is_stable():
    assert make_suggestion_id("br_1", "200") == make_suggestion_id("br_1", "200")


def test_suggestion_id_differs_by_pair():
    assert make_suggestion_id("br_1", "200") != make_suggestion_id("br_1", "201")
    assert make_suggestion_id("br_1", "200") != make_suggestion_id("br_2", "200")


def test_drop_self_matches_uses_external_id():
    result = drop_self_matches({"external_id": "100"}, HITS)
    assert [h["bug_id"] for h in result] == [200]


def test_drop_self_keeps_everything_without_external_id():
    assert len(drop_self_matches({"external_id": None}, HITS)) == 2


def test_fields_say_cosine_similarity_not_probability():
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    fields = build_suggestion_fields(HITS[1], 0.8, now)
    assert fields["similarity"] == 0.9
    assert "not a probability" in fields["score_type"]
    assert fields["threshold"] == 0.8


def test_to_out_maps_id():
    doc = {
        "_id": "dup_1", "report_id": "br_1", "candidate_id": "200",
        "candidate_text": "other report", "similarity": 0.9, "status": "pending",
    }
    out = to_out(doc)
    assert out["id"] == "dup_1"
    assert out["status"] == "pending"
    assert out["candidate_project"] is None


def test_review_request_rejects_unknown_decision():
    with pytest.raises(ValidationError):
        SuggestionReviewRequest(decision="maybe")