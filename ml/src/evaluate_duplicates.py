"""Aap ke lagaye hue labels se duplicate detection ki precision aur recall nikalta hai.

Pehle make_label_sheet.py chalayein, phir ml/data/labels/duplicate_pairs_to_label.csv mein is_duplicate bharein
(1 = duplicate, 0 = nahi, khali = chhod do), phir (repo ke root se):
  python ml/src/evaluate_duplicates.py

Yeh kya naapta hai: "kisi report ka sab se milta julta dusra report, agar similarity T se zyada ho, to kitni baar woh
sach mein duplicate hota hai (precision), aur sab asli duplicate jodon mein se kitne T se upar pakde gaye (recall)".
Jode similarity ke hisson (bands) se barabar chune gaye the, is liye har jore ko uska weight diya jata hai.
Hadd: recall sirf un jodon mein naapa jata hai jin ki similarity 0.5 ya zyada thi. Is se kam similarity wale
asli duplicate yahan nazar hi nahi aate, is liye asli recall is se kam ho sakta hai.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LABEL_DIR = ROOT / "ml" / "data" / "labels"
SHEET_PATH = LABEL_DIR / "duplicate_pairs_to_label.csv"
KEY_PATH = LABEL_DIR / "duplicate_pairs_key.csv"
OUTPUT_PATH = LABEL_DIR / "duplicate_evaluation.json"

THRESHOLDS = [round(0.50 + 0.05 * step, 2) for step in range(10)]  # 0.50 se 0.95
MIN_LABELS = 100
BOOTSTRAPS = 500


def load_labeled(sheet_path=SHEET_PATH, key_path=KEY_PATH):
    sheet = pd.read_csv(sheet_path, encoding="utf-8-sig")
    key = pd.read_csv(key_path, encoding="utf-8")
    data = sheet[["pair_id", "is_duplicate"]].merge(key, on="pair_id", how="inner")
    data["label"] = pd.to_numeric(data["is_duplicate"], errors="coerce")
    return data[data["label"].isin([0, 1])].reset_index(drop=True)


def metrics_at(similarity, label, weight, threshold):
    above = similarity >= threshold
    true_positive = float(weight[above & (label == 1)].sum())
    false_positive = float(weight[above & (label == 0)].sum())
    false_negative = float(weight[~above & (label == 1)].sum())
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive > 0 else None
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative > 0 else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def interval(values):
    clean = [value for value in values if value is not None]
    if len(clean) < 20:
        return None
    return [round(float(np.percentile(clean, 2.5)), 3), round(float(np.percentile(clean, 97.5)), 3)]


def evaluate(data, seed=42):
    similarity = data["similarity"].to_numpy(dtype=float)
    label = data["label"].to_numpy(dtype=int)
    weight = data["weight"].to_numpy(dtype=float)
    rng = np.random.RandomState(seed)
    boot_indexes = [rng.randint(0, len(data), size=len(data)) for _ in range(BOOTSTRAPS)]

    table = []
    for threshold in THRESHOLDS:
        precision, recall, f1 = metrics_at(similarity, label, weight, threshold)
        boot_precision, boot_recall = [], []
        for indexes in boot_indexes:
            p, r, _ = metrics_at(similarity[indexes], label[indexes], weight[indexes], threshold)
            boot_precision.append(p)
            boot_recall.append(r)
        table.append(
            {
                "threshold": threshold,
                "precision": None if precision is None else round(precision, 3),
                "recall": None if recall is None else round(recall, 3),
                "f1": None if f1 is None else round(f1, 3),
                "precision_95_interval": interval(boot_precision),
                "recall_95_interval": interval(boot_recall),
            }
        )
    scored = [row for row in table if row["f1"] is not None]
    best = max(scored, key=lambda row: row["f1"]) if scored else None
    return table, best


def main():
    if not SHEET_PATH.exists() or not KEY_PATH.exists():
        raise SystemExit("Pehle python ml/src/make_label_sheet.py chalayein aur sheet mein labels bharein.")
    data = load_labeled()
    positives = int((data["label"] == 1).sum())
    print(f"Label lagaye gaye jode: {len(data)} (duplicate: {positives}, duplicate nahi: {len(data) - positives})")
    if len(data) == 0 or positives == 0 or positives == len(data):
        raise SystemExit("Naapne ke liye dono tarah ke labels (1 aur 0) chahiye.")

    table, best = evaluate(data)
    print("\nthreshold  precision  recall   f1     (95% interval: precision | recall)")
    for row in table:
        def show(value):
            return "  -  " if value is None else f"{value:5.2f}"

        print(
            f"  {row['threshold']:.2f}      {show(row['precision'])}     {show(row['recall'])}   {show(row['f1'])}   "
            f"{row['precision_95_interval']} | {row['recall_95_interval']}"
        )
    if best:
        print(f"\nSab se behtar F1: threshold {best['threshold']:.2f} (precision {best['precision']}, recall {best['recall']}, F1 {best['f1']})")
    if len(data) < MIN_LABELS:
        print(f"\nDhyan dein: sirf {len(data)} label hain. {MIN_LABELS} se kam par yeh numbers bharose ke qabil nahi.")

    result = {
        "labeled_pairs": int(len(data)),
        "duplicate_pairs": positives,
        "enough_labels": bool(len(data) >= MIN_LABELS),
        "thresholds": table,
        "best_f1": best,
        "note": (
            "Jode sab se milte julte dusre report se bane (similarity 0.5 ya zyada), bands se barabar chune gaye aur weight diye gaye. "
            "Recall sirf in jodon mein naapa gaya, is liye asli recall kam ho sakta hai."
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nNateeja save hua: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
