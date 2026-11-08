"""Upload aur Bulk predict ko aazmane ke liye NAYI reports ki CSV banata hai.

Yeh un reports mein se chunta hai jo aap ki database mein pehle se nahi hain: init_db.py --import-sample ne
ml/data/processed se jo reports (default 2000, seed 42) dali thin, unhein chhod kar baqi mein se. Is liye import ke baad
yeh sab "bina prediction" wali reports hongi, aur Bulk predict ka button chal sakega.

Chalane ka tareeqa (repo ke root se, venv active):
  python scripts/make_test_csv.py                      (500 nayi reports)
  python scripts/make_test_csv.py --rows 1000
  python scripts/make_test_csv.py --with-errors        (3 jaanbujh kar ghalat rows bhi, row errors dekhne ke liye)
  python scripts/make_test_csv.py --exclude sample_data/test_upload_500.csv --seed 8   (pehli file ke baad doosri, alag reports)
  python scripts/make_test_csv.py --source test --rows 400   (sirf test split se: Evaluate page par sachchi naap ke liye)

--source test: reports sirf ml/data/processed/test.csv se aati hain. Model ne in par training nahi ki aur inhein
tuning mein bhi nahi dekha, is liye Evaluate page ka F1 imaandar hota hai. Upload ke liye default (all) behtar hai.
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "ml" / "data" / "processed"
COLUMNS = ["text", "project", "severity", "bug_id"]

BAD_ROWS = [
    {"text": "", "project": "Core", "severity": "major", "bug_id": 990001},                      # text khali
    {"text": "This row has an invalid severity", "project": "Core", "severity": "urgent", "bug_id": 990002},  # ghalat severity
    {"text": "This row has no project and a strange severity", "project": "", "severity": "???", "bug_id": 990003},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--already-imported", type=int, default=2000, help="init_db.py --import-sample ka number")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--exclude", action="append", default=[], help="pehle banayi hui CSV, in ki reports dobara na chunen")
    parser.add_argument("--with-errors", action="store_true")
    parser.add_argument("--source", choices=["all", "test"], default="all")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if args.source == "test":
        remaining = pd.read_csv(PROCESSED / "test.csv", encoding="utf-8")
    else:
        frames = [pd.read_csv(PROCESSED / f"{name}.csv", encoding="utf-8") for name in ("train", "val", "test")]
        everything = pd.concat(frames, ignore_index=True)
        # Bilkul wahi chunav jo backend/init_db.py ka load_sample karta hai.
        imported = everything.sample(n=min(args.already_imported, len(everything)), random_state=42)
        remaining = everything.drop(index=imported.index)

    for path in args.exclude:
        earlier = pd.read_csv(path, encoding="utf-8")
        remaining = remaining[~remaining["bug_id"].isin(earlier["bug_id"])]

    chosen = remaining.sample(n=min(args.rows, len(remaining)), random_state=args.seed)
    result = chosen[COLUMNS].reset_index(drop=True)
    if args.with_errors:
        result = pd.concat([result, pd.DataFrame(BAD_ROWS)], ignore_index=True)

    prefix = "test_split" if args.source == "test" else "test_upload"
    out = Path(args.out) if args.out else ROOT / "sample_data" / f"{prefix}_{args.rows}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False, encoding="utf-8")

    print(f"Save hua: {out}")
    print(f"Nayi reports: {len(chosen)}" + (f" (+ {len(BAD_ROWS)} ghalat rows)" if args.with_errors else ""))
    print("Severity ke hisaab se:")
    print(chosen["severity"].value_counts().to_string())


if __name__ == "__main__":
    main()
