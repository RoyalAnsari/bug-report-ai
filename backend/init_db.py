import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

import pandas as pd  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.collections import INDEXES, ensure_indexes  # noqa: E402
from app.db.mongo import create_client  # noqa: E402
from app.repositories.bug_reports import count_reports, upsert_reports  # noqa: E402

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "ml" / "data" / "processed"


def load_sample(limit):
    frames = [
        pd.read_csv(PROCESSED_DIR / f"{name}.csv", encoding="utf-8")
        for name in ("train", "val", "test")
    ]
    df = pd.concat(frames, ignore_index=True)
    df = df.sample(n=min(limit, len(df)), random_state=42)
    return [
        {"text": r.text, "project": r.project, "severity": r.severity, "external_id": r.bug_id}
        for r in df.itertuples(index=False)
    ]


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-sample", type=int, default=0, help="itni reports database mein dalo")
    args = parser.parse_args()

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        await ensure_indexes(db)
        print("Indexes tayyar hain:")
        for name in INDEXES:
            info = await db[name].index_information()
            print(f"  {name}: {sorted(info)}")

        if args.import_sample:
            reports = load_sample(args.import_sample)
            before = await count_reports(db)
            result = await upsert_reports(db, reports, source="processed_sample")
            after = await count_reports(db)
            print(f"\nBheji gayi reports: {len(reports)}")
            print(f"Naye dakhil hue: {result['inserted']} | pehle se maujood: {result['already_existed']}")
            print(f"bug_reports mein pehle: {before} | ab: {after}")

        print("\nbug_reports total:", await count_reports(db))
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


asyncio.run(main())