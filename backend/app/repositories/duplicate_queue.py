from app.db.collections import BUG_REPORTS, DUPLICATE_SUGGESTIONS
from app.repositories.duplicate_suggestions import to_out


def build_queue_pipeline(status, skip, limit):
    """Pipeline for one page of suggestions, best similarity first, with the text of their report."""
    pipeline = []
    if status:
        pipeline.append({"$match": {"status": status}})
    pipeline += [
        {"$sort": {"similarity": -1, "_id": 1}},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": BUG_REPORTS,
                "localField": "report_id",
                "foreignField": "_id",
                "as": "report",
            }
        },
    ]
    return pipeline


def to_queue_item(doc):
    item = to_out(doc)
    report = doc["report"][0] if doc.get("report") else {}
    item["report_text"] = report.get("text")
    item["report_project"] = report.get("project")
    return item


async def list_queue(db, status=None, page=1, page_size=20):
    query = {"status": status} if status else {}
    total = await db[DUPLICATE_SUGGESTIONS].count_documents(query)
    cursor = await db[DUPLICATE_SUGGESTIONS].aggregate(
        build_queue_pipeline(status, (page - 1) * page_size, page_size)
    )
    items = [to_queue_item(doc) async for doc in cursor]
    return {"items": items, "total": total}
