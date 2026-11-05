"""Duplicate detection ko naapne ke liye report ke jode (pairs) chunta hai, jin par aap khud label lagayenge.

Dataset mein "yeh report us ka duplicate hai" ka koi label nahi hai, is liye precision aur recall nahi nikal sakte.
Yeh script har report ke sab se milte julte dusre report ka jora banati hai, unhein similarity ke 5 hisson (bands)
mein baant kar har hisse se barabar jode chunti hai, aur do file banati hai:

  ml/data/labels/duplicate_pairs_to_label.csv   (aap yeh bharenge: sirf pair_id, do texts, is_duplicate)
  ml/data/labels/duplicate_pairs_key.csv        (similarity aur weight; label lagate waqt isay mat dekhein)

Label lagane ka qaida (is_duplicate column mein):
  1 = dono reports ek hi asal masle ke baare mein hain (ek theek ho to doosra bhi theek ho jaye)
  0 = alag masle hain
  khali = yaqeen nahi, is jore ko chhod dein

Chalane ka tareeqa (repo ke root se, venv active):
  python ml/src/make_label_sheet.py
Phir sheet ko Excel mein kholein, is_duplicate bharein, save karein (CSV hi rehne dein), aur
  python ml/src/evaluate_duplicates.py
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DUPLICATES_DIR = ROOT / "ml" / "artifacts" / "duplicates"
LABEL_DIR = ROOT / "ml" / "data" / "labels"
SHEET_PATH = LABEL_DIR / "duplicate_pairs_to_label.csv"
KEY_PATH = LABEL_DIR / "duplicate_pairs_key.csv"

BANDS = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 1.0001)]


def normalise_text(value):
    return " ".join(str(value).lower().split())


def top_neighbours(embeddings, query_indexes, chunk=256):
    """Har query ke liye sab se milta julta dusra report (khud ko chhod kar) aur cosine similarity."""
    found = []
    for start in range(0, len(query_indexes), chunk):
        batch = query_indexes[start:start + chunk]
        similarity = embeddings[batch] @ embeddings.T
        similarity[np.arange(len(batch)), batch] = -1.0
        best = similarity.argmax(axis=1)
        scores = similarity[np.arange(len(batch)), best]
        found.extend(zip(batch.tolist(), best.tolist(), scores.tolist()))
    return found


def build_sheet(embeddings, reports, queries, per_band, seed):
    rng = np.random.RandomState(seed)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.where(norms == 0, 1.0, norms)

    query_indexes = rng.choice(len(embeddings), size=min(queries, len(embeddings)), replace=False)
    texts = reports["text"].fillna("").map(normalise_text).tolist()

    seen = set()
    candidates = []
    identical = 0
    for a, b, score in top_neighbours(embeddings, query_indexes):
        if score < BANDS[0][0]:
            continue
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        if texts[a] == texts[b]:
            identical += 1  # bilkul ek jaisa text: ise pehchanna aasan hai, is liye label ke liye nahi chuna
            continue
        candidates.append((a, b, float(score)))

    rows, keys = [], []
    for low, high in BANDS:
        in_band = [item for item in candidates if low <= item[2] < high]
        if not in_band:
            continue
        take = min(per_band, len(in_band))
        chosen = rng.choice(len(in_band), size=take, replace=False)
        weight = len(in_band) / take
        for position in chosen:
            a, b, score = in_band[position]
            rows.append((a, b, score, f"{low:.2f}-{min(high, 1.0):.2f}", weight))

    order = rng.permutation(len(rows))
    sheet_rows, key_rows = [], []
    for number, position in enumerate(order, start=1):
        a, b, score, band, weight = rows[position]
        pair_id = f"p{number:04d}"
        sheet_rows.append(
            {
                "pair_id": pair_id,
                "project_a": reports.iloc[a]["project"],
                "text_a": reports.iloc[a]["text"],
                "project_b": reports.iloc[b]["project"],
                "text_b": reports.iloc[b]["text"],
                "is_duplicate": "",
            }
        )
        key_rows.append(
            {
                "pair_id": pair_id,
                "bug_id_a": reports.iloc[a]["bug_id"],
                "bug_id_b": reports.iloc[b]["bug_id"],
                "similarity": round(score, 4),
                "band": band,
                "weight": round(weight, 4),
            }
        )
    return pd.DataFrame(sheet_rows), pd.DataFrame(key_rows), identical, len(candidates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=int, default=3000, help="kitne random reports ke sab se milte jode dekhne hain")
    parser.add_argument("--per-band", type=int, default=40, help="har similarity band se kitne jode label ke liye")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    embeddings = np.load(DUPLICATES_DIR / "embeddings.npy").astype(np.float32)
    reports = pd.read_csv(DUPLICATES_DIR / "reports_index.csv", encoding="utf-8")
    if len(reports) != len(embeddings):
        raise SystemExit(f"reports ({len(reports)}) aur embeddings ({len(embeddings)}) ki tadaad alag hai")

    sheet, key, identical, candidates = build_sheet(embeddings, reports, args.queries, args.per_band, args.seed)
    if sheet.empty:
        raise SystemExit("Koi jora nahi mila (similarity 0.5 se upar).")

    if SHEET_PATH.exists():
        raise SystemExit(f"{SHEET_PATH} pehle se maujood hai. Aap ke labels mit na jayen, is liye pehle usay hata ya naam badal dein.")
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    sheet.to_csv(SHEET_PATH, index=False, encoding="utf-8-sig")
    key.to_csv(KEY_PATH, index=False, encoding="utf-8")

    print(f"Dekhe gaye reports: {min(args.queries, len(embeddings))}")
    print(f"Bilkul ek jaise text wale jode (chhode gaye): {identical}")
    print(f"Baqi jode (similarity 0.5 ya zyada): {candidates}")
    print(key.groupby("band").size().rename("label ke liye chune gaye").to_string())
    print(f"\nKul {len(sheet)} jode. Is file mein is_duplicate bharein:\n  {SHEET_PATH}")


if __name__ == "__main__":
    main()
