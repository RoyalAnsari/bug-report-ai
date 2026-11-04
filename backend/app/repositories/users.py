import uuid
from datetime import datetime, timezone

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
    result = await db[USERS].update_one(
        {"_id": user_id},
        {"$set": {"password_hash": password_hash, "updated_at": datetime.now(timezone.utc)}},
    )
    return result.matched_count == 1


async def touch_login(db, user_id):
    await db[USERS].update_one({"_id": user_id}, {"$set": {"last_login_at": datetime.now(timezone.utc)}})
