import hashlib
from datetime import datetime, timezone

from pymongo import UpdateOne

from app.db.collections import BUG_REPORTS


def normalize_text(text):
    return " ".join(str(text).split())


def make_report_id(project, text):
    """Project aur text se hamesha ek hi ID banati hai (wahi report = wahi ID)."""
    key = f"{str(project or '').strip().lower()}|{normalize_text(text).lower()}"
    return "br_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def build_report_documents(reports, source, now=None):
    """{id: fields} banata hai. Ek hi report do baar ho to ek hi rakhta hai."""
    now = now or datetime.now(timezone.utc)
    documents = {}
    for report in reports:
        text = normalize_text(report["text"])
        project = report.get("project") or None
        fields = {"text": text, "project": project, "source": source, "updated_at": now}
        if report.get("severity"):
            fields["severity"] = report["severity"]
        if report.get("external_id"):
            fields["external_id"] = str(report["external_id"])
        documents[make_report_id(project, text)] = fields
    return documents


def build_upsert_ops(documents, now):
    return [
        UpdateOne(
            {"_id": doc_id},
            {"$set": fields, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        for doc_id, fields in documents.items()
    ]


async def upsert_reports(db, reports, source, batch_size=1000):
    """Reports dalta hai. Pehle se maujood report dobara nahi banti."""
    inserted = 0
    already_existed = 0
    for start in range(0, len(reports), batch_size):
        now = datetime.now(timezone.utc)
        documents = build_report_documents(reports[start : start + batch_size], source, now)
        if not documents:
            continue
        result = await db[BUG_REPORTS].bulk_write(build_upsert_ops(documents, now), ordered=False)
        inserted += result.upserted_count
        already_existed += result.matched_count
    return {"inserted": inserted, "already_existed": already_existed}


async def count_reports(db):
    return await db[BUG_REPORTS].count_documents({})