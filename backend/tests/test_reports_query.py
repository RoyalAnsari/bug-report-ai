from datetime import datetime, timezone

import pytest

from app.repositories.report_crud import build_filter, build_sort, page_count, to_out


def test_filter_empty_when_nothing_given():
    assert build_filter() == {}


def test_filter_combines_all_conditions():
    assert build_filter("crash", "Core", "major") == {
        "$text": {"$search": "crash"},
        "project": "Core",
        "severity": "major",
    }


def test_filter_ignores_blank_search():
    assert build_filter("   ") == {}


def test_sort_default_is_newest_first_with_stable_tiebreak():
    assert build_sort() == [("created_at", -1), ("_id", 1)]


def test_sort_ascending():
    assert build_sort("project", "asc") == [("project", 1), ("_id", 1)]


def test_sort_rejects_unknown_field():
    with pytest.raises(ValueError):
        build_sort("password")


def test_page_count():
    assert page_count(0, 20) == 0
    assert page_count(20, 20) == 1
    assert page_count(21, 20) == 2


def test_to_out_maps_id_and_fields():
    now = datetime.now(timezone.utc)
    out = to_out({"_id": "br_1", "text": "Crash", "project": "Core", "created_at": now})
    assert out["id"] == "br_1"
    assert out["text"] == "Crash"
    assert out["severity"] is None
    assert out["created_at"] == now