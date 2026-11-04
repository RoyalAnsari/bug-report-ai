"""Kisi bhi user ka password reset karta hai (khaas kar jab admin khud apna password bhool jaye).

Yeh script sirf us computer par chalti hai jis ke paas database ki .env maujood hai, is liye yeh
login ke baghair bhi mehfooz hai. Reset ke baad purane tokens band ho jate hain aur account unlock ho jata hai.

Chalane ka tareeqa (backend folder se):
    python reset_password.py
    python reset_password.py --activate     # deactivated user ko dobara active bhi karna ho to
"""
import argparse
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
from app.db.mongo import create_client  # noqa: E402
from app.repositories import users as users_repo  # noqa: E402
from app.schemas.auth import PasswordSet  # noqa: E402


def ask_new_password():
    password = getpass.getpass("Naya password (kam se kam 12 characters): ")
    again = getpass.getpass("Naya password dobara: ")
    if password != again:
        print("Dono passwords alag hain.")
        raise SystemExit(1)
    try:
        return PasswordSet(new_password=password).new_password
    except ValidationError as error:
        for problem in error.errors():
            print(f"- {problem['msg']}")
        raise SystemExit(1)


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true", help="user deactivated ho to usay dobara active karo")
    args = parser.parse_args()

    email = input("User ka email: ").strip()
    if not email:
        print("Email likhna zaroori hai.")
        raise SystemExit(1)

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        user = await users_repo.get_by_email(db, email)
        if user is None:
            print("Is email ka koi user nahi mila. Maujooda users:")
            for existing in await users_repo.list_users(db):
                print(f"  {existing['email']} ({existing['role']})")
            raise SystemExit(1)

        if not user.get("is_active", True):
            if args.activate:
                await users_repo.update_user(db, user["_id"], {"is_active": True})
                print("User dobara active kar diya gaya.")
            else:
                print("Dhyan dein: yeh user deactivated hai. Login ke liye --activate ke saath chalayein.")

        new_password = ask_new_password()
        await users_repo.set_password(db, user["_id"], hash_password(new_password))
        print(f"Password badal gaya: {user['email']}. Ab naye password se login karein.")
    except SystemExit:
        raise
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


asyncio.run(main())
