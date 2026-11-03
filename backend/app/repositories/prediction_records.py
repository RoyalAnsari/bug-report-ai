import uuid
from datetime import datetime, timezone

from app.db.collections import PREDICTIONS

SEVERITY_MODEL_VERSION = "tfidf-linearsvc-v1"  # haath se rakha naam, model_versions baad mein


def build_prediction_document(report_id, result, model_version=SEVERITY_MODEL_VERSION, now=None):
    """Ek prediction ka document banata hai (database mein dalne se pehle)."""
    return {
        "_id": "pred_" + uuid.uuid4().hex[:20],
        "report_id": report_id,
        "label": result["label"],
        "margin": result["margin"],
        "needs_review": result["needs_review"],
        "scores": result["scores"],
        "model_version": model_version,
        "created_at": now or datetime.now(timezone.utc),
    }


def to_out(doc):
    return {
        "id": doc["_id"],
        "report_id": doc["report_id"],
        "label": doc["label"],
        "margin": doc["margin"],
        "needs_review": doc["needs_review"],
        "scores": doc["scores"],
        "model_version": doc["model_version"],
        "created_at": doc.get("created_at"),
    }


async def save_prediction(db, report_id, result, model_version=SEVERITY_MODEL_VERSION):
    document = build_prediction_document(report_id, result, model_version)
    await db[PREDICTIONS].insert_one(document)
    return to_out(document)


async def list_predictions(db, report_id, limit=20):
    cursor = (
        db[PREDICTIONS]
        .find({"report_id": report_id})
        .sort([("created_at", -1), ("_id", 1)])
        .limit(limit)
    )
    return [to_out(doc) async for doc in cursor]