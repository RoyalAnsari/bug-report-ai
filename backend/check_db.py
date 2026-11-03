import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

from app.core.config import Settings  # noqa: E402
from app.db.mongo import create_client, ping  # noqa: E402


async def main():
    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    try:
        await ping(client, settings.mongodb_db)
        print("MongoDB se rabta theek hai. Database:", settings.mongodb_db)
    except Exception as error:
        # Connection string print nahi karte, sirf error ki kism
        details = getattr(error, "details", None)
        code_name = details.get("codeName") if isinstance(details, dict) else None
        print("MongoDB se rabta nahi hua:", type(error).__name__, getattr(error, "code", None), code_name)
        raise SystemExit(1)
    finally:
        await client.close()


asyncio.run(main())