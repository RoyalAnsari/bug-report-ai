from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.db.collections import BUG_REPORTS, PREDICTIONS, REVIEW_FEEDBACK


def resolve_final_label(predicted_label, action, label):
    """Confirm par predicted label, correct par reviewer ka label."""
    return predicted_label if action == "confirm" else label


def build_feedback_document(prediction, action, final_label, note=None, now=None):
    """Feedback ki ID prediction ki ID se banti hai, isliye ek prediction ka ek hi review ho sakta hai."""
    return {
        "_id": "fb_" + prediction["_id"],
        "target_type": "prediction",
        "target_id": prediction["_id"],
        "report_id": prediction["report_id"],
        "action": action,
        "predicted_label": prediction["label"],
        "final_label": final_label,
        "note": note,
        "created_at": now or datetime.now(timezone.utc),
    }


def to_out(doc):
    return {
        "id": doc["_id"],
        "prediction_id": doc["target_id"],
        "report_id": doc["report_id"],
        "action": doc["action"],
        "predicted_label": doc["predicted_label"],
        "final_label": doc["final_label"],
        "note": doc.get("note"),
        "created_at": doc.get("created_at"),
    }


async def submit_review(db, prediction_id, action, label, note=None):
    """Wapas deta hai: ("ok", review) ya ("not_found", None) ya ("exists", None)."""
    prediction = await db[PREDICTIONS].find_one({"_id": prediction_id})
    if prediction is None:
        return "not_found", None

    final_label = resolve_final_label(prediction["label"], action, label)
    document = build_feedback_document(prediction, action, final_label, note)
    try:
        await db[REVIEW_FEEDBACK].insert_one(document)
    except DuplicateKeyError:
        return "exists", None

    await db[BUG_REPORTS].update_one(
        {"_id": prediction["report_id"]},
        {"$set": {"severity": final_label, "updated_at": datetime.now(timezone.utc)}},
    )
    return "ok", to_out(document)


async def get_review(db, prediction_id):
    doc = await db[REVIEW_FEEDBACK].find_one({"_id": "fb_" + prediction_id})
    return to_out(doc) if doc else None