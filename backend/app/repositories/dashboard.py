from app.db.collections import (
    BUG_REPORTS,
    DUPLICATE_SUGGESTIONS,
    PREDICTIONS,
    REVIEW_FEEDBACK,
)
from app.services.csv_validation import ALLOWED_SEVERITIES

DUPLICATE_STATUSES = ("pending", "confirmed", "rejected")


def fill_severity_counts(rows):
    """[{"_id": label, "count": n}] ko chhe labels + unlabeled ki poori dictionary banata hai."""
    counts = {label: 0 for label in ALLOWED_SEVERITIES}
    counts["unlabeled"] = 0
    for row in rows:
        key = row["_id"]
        if key in ALLOWED_SEVERITIES:
            counts[key] += row["count"]
        else:
            counts["unlabeled"] += row["count"]
    return counts


def fill_status_counts(rows):
    """Duplicate suggestions ki ginti. Jo status maloom nahi, wo 'other' mein jata hai."""
    counts = {status: 0 for status in DUPLICATE_STATUSES}
    for row in rows:
        key = row["_id"] if row["_id"] in DUPLICATE_STATUSES else "other"
        counts[key] = counts.get(key, 0) + row["count"]
    return counts


def build_pending_review_pipeline():
    """Un reports ki ginti jin ki aakhri prediction ko review chahiye aur feedback nahi mila."""
    return [
        {"$sort": {"report_id": 1, "created_at": -1}},
        {
            "$group": {
                "_id": "$report_id",
                "prediction_id": {"$first": "$_id"},
                "needs_review": {"$first": "$needs_review"},
            }
        },
        {"$match": {"needs_review": True}},
        {
            "$lookup": {
                "from": REVIEW_FEEDBACK,
                "let": {"pid": "$prediction_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$target_type", "prediction"]},
                                    {"$eq": ["$target_id", "$$pid"]},
                                ]
                            }
                        }
                    },
                    {"$limit": 1},
                ],
                "as": "feedback",
            }
        },
        {"$match": {"feedback": {"$size": 0}}},
        {"$count": "n"},
    ]


async def _rows(collection, pipeline):
    cursor = await collection.aggregate(pipeline)
    return [doc async for doc in cursor]


async def _first_count(collection, pipeline):
    rows = await _rows(collection, pipeline)
    return rows[0]["n"] if rows else 0


async def get_summary(db):
    total_reports = await db[BUG_REPORTS].count_documents({})
    severity_rows = await _rows(
        db[BUG_REPORTS], [{"$group": {"_id": "$severity", "count": {"$sum": 1}}}]
    )
    predictions_total = await db[PREDICTIONS].count_documents({})
    reports_with_predictions = await _first_count(
        db[PREDICTIONS], [{"$group": {"_id": "$report_id"}}, {"$count": "n"}]
    )
    pending_reviews = await _first_count(db[PREDICTIONS], build_pending_review_pipeline())
    duplicate_rows = await _rows(
        db[DUPLICATE_SUGGESTIONS], [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    )
    duplicates = fill_status_counts(duplicate_rows)

    return {
        "total_reports": total_reports,
        "severity_distribution": fill_severity_counts(severity_rows),
        "predictions_total": predictions_total,
        "reports_with_predictions": reports_with_predictions,
        "pending_reviews": pending_reviews,
        "duplicate_suggestions": duplicates,
        "duplicate_suggestions_total": sum(duplicates.values()),
    }