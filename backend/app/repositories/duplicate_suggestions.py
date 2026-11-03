import hashlib
from datetime import datetime, timezone

from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError

from app.db.collections import DUPLICATE_SUGGESTIONS, REVIEW_FEEDBACK

SCORE_TYPE = "cosine similarity (not a probability)"
DUPLICATE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DECISION_TO_STATUS = {"confirm": "confirmed", "reject": "rejected"}


def make_suggestion_id(report_id, candidate_id):
    """Ek pair ki hamesha ek hi ID banti hai."""
    key = f"{report_id}|{candidate_id}"
    return "dup_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def drop_self_matches(report, hits):
    """Report ko uski apni candidate list se nikalta hai (external_id ki madad se)."""
    own = str(report.get("external_id") or "")
    if not own:
        return list(hits)
    return [hit for hit in hits if str(hit["bug_id"]) != own]


def build_suggestion_fields(hit, threshold, now):
    return {
        "candidate_text": hit["text"],
        "candidate_project": hit.get("project"),
        "similarity": hit["similarity"],
        "score_type": SCORE_TYPE,
        "threshold": threshold,
        "model": DUPLICATE_MODEL,
        "updated_at": now,
    }


def to_out(doc):
    return {
        "id": doc["_id"],
        "report_id": doc["report_id"],
        "candidate_id": doc["candidate_id"],
        "candidate_text": doc["candidate_text"],
        "candidate_project": doc.get("candidate_project"),
        "similarity": doc["similarity"],
        "score_type": doc.get("score_type", SCORE_TYPE),
        "status": doc["status"],
        "created_at": doc.get("created_at"),
    }


async def save_candidates(db, report_id, hits, threshold):
    """Candidates dalta hai. Pehle se maujood pair ka status nahi badalta."""
    if not hits:
        return {"inserted": 0, "existing": 0}
    now = datetime.now(timezone.utc)
    operations = []
    for hit in hits:
        candidate_id = str(hit["bug_id"])
        operations.append(
            UpdateOne(
                {"_id": make_suggestion_id(report_id, candidate_id)},
                {
                    "$set": build_suggestion_fields(hit, threshold, now),
                    "$setOnInsert": {
                        "report_id": report_id,
                        "candidate_id": candidate_id,
                        "status": "pending",
                        "created_at": now,
                    },
                },
                upsert=True,
            )
        )
    result = await db[DUPLICATE_SUGGESTIONS].bulk_write(operations, ordered=False)
    return {"inserted": result.upserted_count, "existing": result.matched_count}


async def list_suggestions(db, report_id, status=None):
    query = {"report_id": report_id}
    if status:
        query["status"] = status
    cursor = db[DUPLICATE_SUGGESTIONS].find(query).sort([("similarity", -1), ("_id", 1)])
    return [to_out(doc) async for doc in cursor]


async def review_suggestion(db, suggestion_id, decision, note=None):
    """Wapas deta hai: ("ok", suggestion) ya ("not_found", None) ya ("exists", None)."""
    suggestion = await db[DUPLICATE_SUGGESTIONS].find_one({"_id": suggestion_id})
    if suggestion is None:
        return "not_found", None

    now = datetime.now(timezone.utc)
    feedback = {
        "_id": "fb_" + suggestion_id,
        "target_type": "duplicate_suggestion",
        "target_id": suggestion_id,
        "report_id": suggestion["report_id"],
        "action": decision,
        "note": note,
        "created_at": now,
    }
    try:
        await db[REVIEW_FEEDBACK].insert_one(feedback)
    except DuplicateKeyError:
        return "exists", None

    updated = await db[DUPLICATE_SUGGESTIONS].find_one_and_update(
        {"_id": suggestion_id},
        {"$set": {"status": DECISION_TO_STATUS[decision], "reviewed_at": now}},
        return_document=True,
    )
    return "ok", to_out(updated)