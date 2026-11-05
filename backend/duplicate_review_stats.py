"""Aap ne duplicate suggestions par jo confirm ya reject kiya, un se app ki precision dekhta hai.

Chalane ka tareeqa (backend folder se):
    python duplicate_review_stats.py
    python duplicate_review_stats.py --export ../ml/data/labels/reviewed_suggestions.csv

Dhyan dein: app sirf woh jode dikhata hai jin ki similarity uske threshold (default 0.80) se upar ho, aur woh bhi random
nahi. Is liye yeh sirf batata hai ke "app jo suggestions deta hai, un mein se kitne sahi nikle". Isse recall nahi
nikalta, aur 0.80 se neeche ki similarity ke baare mein kuch nahi pata chalta (uske liye make_label_sheet.py hai).
"""
import argparse
import asyncio
import csv
import math
import sys
from pathlib import Path

BAND_WIDTH = 0.05
MIN_REVIEWS = 30


def wilson_interval(successes, total, z=1.96):
    """Chhote sample ke liye bhi theek rehne wala 95% daiyra (interval)."""
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def band_of(similarity):
    low = math.floor(round(similarity / BAND_WIDTH, 6)) * BAND_WIDTH
    low = min(low, 1.0 - BAND_WIDTH)
    return round(low, 2)


def summarize(rows):
    """rows: (similarity, status) ki list, status 'confirmed' ya 'rejected'. Band ke hisaab se ginti wapas deta hai."""
    bands = {}
    for similarity, status in rows:
        entry = bands.setdefault(band_of(similarity), {"confirmed": 0, "rejected": 0})
        entry[status] += 1
    result = []
    for low in sorted(bands):
        confirmed, rejected = bands[low]["confirmed"], bands[low]["rejected"]
        total = confirmed + rejected
        result.append(
            {
                "band": f"{low:.2f}-{low + BAND_WIDTH:.2f}",
                "confirmed": confirmed,
                "rejected": rejected,
                "precision": confirmed / total,
                "interval": wilson_interval(confirmed, total),
            }
        )
    confirmed_all = sum(1 for _, status in rows if status == "confirmed")
    total_all = len(rows)
    overall = None
    if total_all:
        overall = {
            "confirmed": confirmed_all,
            "rejected": total_all - confirmed_all,
            "precision": confirmed_all / total_all,
            "interval": wilson_interval(confirmed_all, total_all),
        }
    return result, overall


def format_interval(interval):
    return "-" if interval is None else f"{interval[0]:.2f} se {interval[1]:.2f}"


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", help="reviewed jode CSV file mein save karo (text ke saath)")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")

    from app.core.config import Settings
    from app.db.collections import BUG_REPORTS, DUPLICATE_SUGGESTIONS
    from app.db.mongo import create_client

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        reviewed = [
            doc async for doc in db[DUPLICATE_SUGGESTIONS].find({"status": {"$in": ["confirmed", "rejected"]}})
        ]
        pending = await db[DUPLICATE_SUGGESTIONS].count_documents({"status": "pending"})

        print(f"Review ho chuke: {len(reviewed)}   Abhi baqi (pending): {pending}")
        if not reviewed:
            print("Abhi koi suggestion confirm ya reject nahi hui.")
            return

        rows = [(float(doc["similarity"]), doc["status"]) for doc in reviewed]
        bands, overall = summarize(rows)

        print("\nSimilarity     confirm  reject   precision   95% daira")
        for entry in bands:
            print(
                f"{entry['band']}      {entry['confirmed']:5d}   {entry['rejected']:5d}     {entry['precision']:5.2f}      "
                f"{format_interval(entry['interval'])}"
            )
        print(
            f"\nKul: {overall['confirmed']} confirm, {overall['rejected']} reject, precision {overall['precision']:.2f} "
            f"(95% daira {format_interval(overall['interval'])})"
        )
        if len(reviewed) < MIN_REVIEWS:
            print(f"\nDhyan dein: sirf {len(reviewed)} reviews hain. {MIN_REVIEWS} se kam par yeh numbers bharose ke qabil nahi.")
        print("\nYaad rakhein: yeh sirf app ki dikhai hui suggestions ki precision hai. Recall is se nahi nikalta.")

        if args.export:
            report_ids = list({doc["report_id"] for doc in reviewed})
            texts = {}
            async for report in db[BUG_REPORTS].find({"_id": {"$in": report_ids}}):
                texts[report["_id"]] = report.get("text", "")
            path = Path(args.export)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["status", "similarity", "report_id", "text_a", "candidate_id", "text_b"])
                for doc in sorted(reviewed, key=lambda item: -float(item["similarity"])):
                    writer.writerow(
                        [
                            doc["status"],
                            round(float(doc["similarity"]), 4),
                            doc["report_id"],
                            texts.get(doc["report_id"], ""),
                            doc["candidate_id"],
                            doc.get("candidate_text", ""),
                        ]
                    )
            print(f"\nSave hua: {path}")
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
