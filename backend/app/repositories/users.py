import uuid
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.db.collections import USERS


def normalize_email(email):
    return email.strip().lower()


def to_public(doc):
    """API ke jawab ke liye. password_hash kabhi bahar nahi jata."""
    return {
        "id": doc["_id"],
        "email": doc["email"],
        "name": doc["name"],
        "role": doc["role"],
        "is_active": doc.get("is_active", True),
        "created_at": doc.get("created_at"),
        "last_login_at": doc.get("last_login_at"),
    }


async def get_by_id(db, user_id):
    return await db[USERS].find_one({"_id": user_id})


async def get_by_email(db, email):
    return await db[USERS].find_one({"email": normalize_email(email)})


async def create_user(db, email, name, role, password_hash):
    """Naya user banata hai. Wahi email pehle se ho to None wapas deta hai."""
    now = datetime.now(timezone.utc)
    document = {
        "_id": "usr_" + uuid.uuid4().hex[:20],
        "email": normalize_email(email),
        "name": name,
        "role": role,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "failed_logins": 0,
        "locked_until": None,
    }
    try:
        await db[USERS].insert_one(document)
    except DuplicateKeyError:
        return None
    return document


async def list_users(db):
    cursor = db[USERS].find({}).sort([("created_at", 1), ("_id", 1)])
    return [doc async for doc in cursor]


async def update_user(db, user_id, fields):
    return await db[USERS].find_one_and_update(
        {"_id": user_id},
        {"$set": {**fields, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )


async def set_password(db, user_id, password_hash):
    """Naya password rakhta hai. Purane tokens band ho jate hain aur account unlock ho jata hai."""
    now = datetime.now(timezone.utc)
    result = await db[USERS].update_one(
        {"_id": user_id},
        {
            "$set": {
                "password_hash": password_hash,
                "password_changed_at": now,
                "updated_at": now,
                "failed_logins": 0,
                "locked_until": None,
            }
        },
    )
    return result.matched_count == 1


async def touch_login(db, user_id):
    """Kamyab login: waqt likhta hai aur ghalat koshishon ki ginti saaf karta hai."""
    await db[USERS].update_one(
        {"_id": user_id},
        {"$set": {"last_login_at": datetime.now(timezone.utc), "failed_logins": 0, "locked_until": None}},
    )


async def register_failed_login(db, user_id, max_failed, lock_minutes):
    """Ghalat password ginta hai. Had poori ho to account lock karke lock ka waqt wapas deta hai."""
    updated = await db[USERS].find_one_and_update(
        {"_id": user_id},
        {"$inc": {"failed_logins": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None or updated.get("failed_logins", 0) < max_failed:
        return None
    locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
    await db[USERS].update_one(
        {"_id": user_id},
        {"$set": {"locked_until": locked_until, "failed_logins": 0}},
    )
    return locked_until
