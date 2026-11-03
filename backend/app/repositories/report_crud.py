from datetime import datetime, timezone
from math import ceil

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.db.collections import (
    BUG_REPORTS,
    DUPLICATE_SUGGESTIONS,
    PREDICTIONS,
    REVIEW_FEEDBACK,
)
from app.repositories.bug_reports import build_report_documents

SORT_FIELDS = ("created_at", "updated_at", "project", "severity")


def build_filter(search=None, project=None, severity=None):
    """MongoDB ka filter banata hai."""
    query = {}
    if search and search.strip():
        query["$text"] = {"$search": search.strip()}
    if project:
        query["project"] = project
    if severity:
        query["severity"] = severity
    return query


def build_sort(sort_by="created_at", order="desc"):
    """Sort ki list banata hai. _id aakhir mein hai, taake pages ka order stable rahe."""
    if sort_by not in SORT_FIELDS:
        raise ValueError(f"sort_by must be one of {SORT_FIELDS}")
    direction = -1 if order == "desc" else 1
    return [(sort_by, direction), ("_id", 1)]


def page_count(total, page_size):
    return ceil(total / page_size) if total > 0 else 0


def to_out(doc):
    """MongoDB ke document ko API ke jawab ki shakl deta hai."""
    return {
        "id": doc["_id"],
        "text": doc.get("text"),
        "project": doc.get("project"),
        "severity": doc.get("severity"),
        "external_id": doc.get("external_id"),
        "source": doc.get("source"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def list_reports(db, page=1, page_size=20, search=None, project=None,
                       severity=None, sort_by="created_at", order="desc"):
    query = build_filter(search, project, severity)
    collection = db[BUG_REPORTS]
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort(build_sort(sort_by, order))
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = [to_out(doc) async for doc in cursor]
    return {"items": items, "total": total}


async def get_report(db, report_id):
    doc = await db[BUG_REPORTS].find_one({"_id": report_id})
    return to_out(doc) if doc else None


async def create_report(db, data):
    """Nayi report banata hai. Wahi report pehle se ho to None wapas deta hai."""
    now = datetime.now(timezone.utc)
    documents = build_report_documents([data], "manual", now)
    report_id, fields = next(iter(documents.items()))
    document = {"_id": report_id, **fields, "created_at": now}
    try:
        await db[BUG_REPORTS].insert_one(document)
    except DuplicateKeyError:
        return None
    return to_out(document)


async def update_severity(db, report_id, severity):
    doc = await db[BUG_REPORTS].find_one_and_update(
        {"_id": report_id},
        {"$set": {"severity": severity, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    return to_out(doc) if doc else None


async def delete_report(db, report_id):
    """Report hatata hai, aur us ki predictions, duplicate suggestions aur reviews bhi."""
    await db[PREDICTIONS].delete_many({"report_id": report_id})
    await db[DUPLICATE_SUGGESTIONS].delete_many({"report_id": report_id})
    await db[REVIEW_FEEDBACK].delete_many({"report_id": report_id})
    result = await db[BUG_REPORTS].delete_one({"_id": report_id})
    return result.deleted_count == 1