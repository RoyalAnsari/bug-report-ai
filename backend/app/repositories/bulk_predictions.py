from app.db.collections import BUG_REPORTS, PREDICTIONS


async def count_unpredicted(db):
    """How many reports have a prediction and how many do not."""
    total = await db[BUG_REPORTS].count_documents({})
    predicted_ids = await db[PREDICTIONS].distinct("report_id")
    with_predictions = (
        await db[BUG_REPORTS].count_documents({"_id": {"$in": predicted_ids}}) if predicted_ids else 0
    )
    return {
        "total_reports": total,
        "reports_with_predictions": with_predictions,
        "unpredicted": total - with_predictions,
    }


async def find_unpredicted(db, limit):
    """Up to 'limit' reports that have no prediction yet, always in the same order."""
    predicted_ids = await db[PREDICTIONS].distinct("report_id")
    cursor = (
        db[BUG_REPORTS]
        .find({"_id": {"$nin": predicted_ids}}, {"text": 1, "project": 1})
        .sort("_id", 1)
        .limit(limit)
    )
    return [
        {"id": doc["_id"], "text": doc["text"], "project": doc.get("project")}
        async for doc in cursor
    ]


async def save_many(db, documents):
    if documents:
        await db[PREDICTIONS].insert_many(documents, ordered=False)
