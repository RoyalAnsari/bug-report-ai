from app.repositories.dashboard import (
    build_pending_review_pipeline,
    fill_severity_counts,
    fill_status_counts,
)


def test_severity_counts_fill_all_labels_with_zero():
    counts = fill_severity_counts([{"_id": "major", "count": 5}])
    assert counts["major"] == 5
    assert counts["blocker"] == 0
    assert counts["unlabeled"] == 0
    assert set(counts) == {"blocker", "critical", "major", "normal", "minor", "trivial", "unlabeled"}


def test_severity_counts_put_missing_and_unknown_in_unlabeled():
    counts = fill_severity_counts(
        [{"_id": None, "count": 3}, {"_id": "urgent", "count": 2}, {"_id": "minor", "count": 1}]
    )
    assert counts["unlabeled"] == 5
    assert counts["minor"] == 1


def test_status_counts_default_to_zero():
    assert fill_status_counts([]) == {"pending": 0, "confirmed": 0, "rejected": 0}


def test_status_counts_unknown_status_goes_to_other():
    counts = fill_status_counts([{"_id": "confirmed", "count": 2}, {"_id": "weird", "count": 4}])
    assert counts["confirmed"] == 2
    assert counts["other"] == 4


def test_pending_pipeline_uses_latest_prediction_and_ends_with_count():
    pipeline = build_pending_review_pipeline()
    assert pipeline[0] == {"$sort": {"report_id": 1, "created_at": -1}}
    assert {"$match": {"needs_review": True}} in pipeline
    assert pipeline[-1] == {"$count": "n"}