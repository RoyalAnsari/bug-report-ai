"""Database ki backup JSON lines files mein banata hai (har collection ki ek file).

Chalane ka tareeqa (backend folder se):
    python backup_db.py
    python backup_db.py --include-users

Backup backups/<waqt>/ mein jati hai (repo ke root mein; Git mein nahi jati). Users ki backup mein password hash nahi hota
(yeh jaanbujh kar hai), is liye backup se logins wapas nahi aate; admin dobara banane parte hain (create_admin.py).
Backup mein bug reports ka text hota hai, is liye usay mehfooz jagah rakhein.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[1]


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-users", action="store_true", help="users ki list bhi (password hash ke baghair)")
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "backups"))
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")

    from bson import json_util

    from app.core.config import Settings
    from app.db.collections import (
        BUG_REPORTS,
        DUPLICATE_SUGGESTIONS,
        MODEL_VERSIONS,
        PREDICTIONS,
        REVIEW_FEEDBACK,
        USERS,
    )
    from app.db.mongo import create_client

    names = [BUG_REPORTS, PREDICTIONS, DUPLICATE_SUGGESTIONS, REVIEW_FEEDBACK, MODEL_VERSIONS]
    if args.include_users:
        names.append(USERS)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = Path(args.out_dir) / stamp
    target.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        for name in names:
            count = 0
            with (target / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
                async for document in db[name].find({}):
                    document.pop("password_hash", None)
                    handle.write(json_util.dumps(document, ensure_ascii=False) + "\n")
                    count += 1
            print(f"{name}: {count} documents")
        print(f"\nBackup tayyar: {target}")
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
