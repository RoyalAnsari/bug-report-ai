from datetime import datetime, timezone

APP_SETTINGS = "app_settings"
DOCUMENT_ID = "app"


async def get_saved(db):
    """The saved settings document, or an empty dictionary when nothing was saved."""
    document = await db[APP_SETTINGS].find_one({"_id": DOCUMENT_ID})
    return document or {}


async def save(db, values):
    now = datetime.now(timezone.utc)
    await db[APP_SETTINGS].update_one(
        {"_id": DOCUMENT_ID},
        {"$set": {**values, "updated_at": now}},
        upsert=True,
    )
    return now


async def clear(db):
    await db[APP_SETTINGS].delete_one({"_id": DOCUMENT_ID})
