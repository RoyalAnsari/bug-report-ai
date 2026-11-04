"""Pehla admin user banata hai. Login ke liye public signup nahi hai, is liye yeh ek baar chalana zaroori hai.

Chalane ka tareeqa (backend folder se):
    python create_admin.py
"""
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

from pydantic import ValidationError  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.collections import ensure_indexes  # noqa: E402
from app.db.mongo import create_client  # noqa: E402
from app.repositories import users as users_repo  # noqa: E402
from app.schemas.auth import UserCreate  # noqa: E402


def ask_details():
    email = input("Admin email: ").strip()
    name = input("Admin name: ").strip()
    password = getpass.getpass("Password (kam se kam 12 characters): ")
    again = getpass.getpass("Password dobara: ")
    if password != again:
        print("Dono passwords alag hain.")
        raise SystemExit(1)
    try:
        return UserCreate(email=email, name=name, role="admin", password=password)
    except ValidationError as error:
        for problem in error.errors():
            print(f"- {'.'.join(str(p) for p in problem['loc'])}: {problem['msg']}")
        raise SystemExit(1)


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    details = ask_details()

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        await ensure_indexes(db)
        created = await users_repo.create_user(
            db, details.email, details.name, "admin", hash_password(details.password)
        )
        if created is None:
            print("Is email ka user pehle se maujood hai.")
            raise SystemExit(1)
        print(f"Admin ban gaya: {created['email']}")
    except SystemExit:
        raise
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


asyncio.run(main())
