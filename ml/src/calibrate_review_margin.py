"""Transformer ke liye "Needs review" ka margin chunta hai.

Margin = sab se upar aur dusri class ki probability ka farq (0 se 1). Margin se kam ho to prediction "Needs review"
hoti hai. Yeh script validation par dikhati hai ke har margin par kitni predictions flag hoti hain, aur flag na hui
predictions kitni sahi hain (flag hui kam sahi honi chahiyen). Phir ek default chunti hai.

Pehle Colab ki chhoti zip (val_logits.npy, test_logits.npy, val_labels.npy, test_labels.npy, offsets.json)
ml/artifacts/severity_transformer mein extract honi chahiye.

Chalane ka tareeqa (repo ke root se):
  python ml/src/calibrate_review_margin.py              (15% predictions review ke liye)
  python ml/src/calibrate_review_margin.py --share 0.10 (10% predictions)
"""
import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "ml" / "artifacts" / "severity_transformer"
SHARES = [0.05, 0.10, 0.15, 0.20, 0.30]


def probability_gaps(logits, offsets):
    scores = np.asarray(logits, dtype=np.float64) + np.asarray(offsets, dtype=np.float64)
    shifted = scores - scores.max(axis=1, keepdims=True)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    ordered = -np.sort(-probabilities, axis=1)
    return ordered[:, 0] - ordered[:, 1], scores.argmax(axis=1)


def split_numbers(gaps, predictions, labels, margin):
    flagged = gaps < margin
    correct = predictions == labels

    def accuracy(mask):
        return float(correct[mask].mean()) if mask.any() else float("nan")

    return {
        "flagged_share": float(flagged.mean()),
        "accuracy_flagged": accuracy(flagged),
        "accuracy_not_flagged": accuracy(~flagged),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", type=float, default=0.15, help="validation ki kitni predictions review ke liye hon (0 se 1)")
    parser.add_argument("--dir", default=str(DIRECTORY))
    args = parser.parse_args()
    if not 0.0 < args.share < 1.0:
        raise SystemExit("--share 0 aur 1 ke beech hona chahiye")

    directory = Path(args.dir)
    needed = ["val_logits.npy", "test_logits.npy", "val_labels.npy", "test_labels.npy", "offsets.json"]
    absent = [name for name in needed if not (directory / name).exists()]
    if absent:
        raise SystemExit(f"{directory} mein yeh files nahi hain: {absent}")

    offsets = json.loads((directory / "offsets.json").read_text(encoding="utf-8"))
    val_gaps, val_pred = probability_gaps(np.load(directory / "val_logits.npy"), offsets)
    test_gaps, test_pred = probability_gaps(np.load(directory / "test_logits.npy"), offsets)
    y_val = np.load(directory / "val_labels.npy")
    y_test = np.load(directory / "test_labels.npy")

    print(f"Sab predictions ki accuracy: validation {float((val_pred == y_val).mean()):.3f}, test {float((test_pred == y_test).mean()):.3f}\n")
    print("Review ka hissa   margin   |  validation: sahi (flag na hui)  sahi (flag hui)  |  test: flag hissa  sahi (flag na hui)  sahi (flag hui)")
    for share in SHARES:
        margin = float(np.quantile(val_gaps, share))
        val_numbers = split_numbers(val_gaps, val_pred, y_val, margin)
        test_numbers = split_numbers(test_gaps, test_pred, y_test, margin)
        print(
            f"   {share:4.0%}          {margin:.3f}   |        {val_numbers['accuracy_not_flagged']:.3f}                     "
            f"{val_numbers['accuracy_flagged']:.3f}        |      {test_numbers['flagged_share']:5.1%}            "
            f"{test_numbers['accuracy_not_flagged']:.3f}               {test_numbers['accuracy_flagged']:.3f}"
        )

    margin = round(float(np.quantile(val_gaps, args.share)), 4)
    chosen_test = split_numbers(test_gaps, test_pred, y_test, margin)
    result = {
        "default": margin,
        "method": f"validation par probability gap ka {args.share:.0%} quantile",
        "validation_flagged_share": args.share,
        "test_flagged_share": round(chosen_test["flagged_share"], 4),
        "test_accuracy_flagged": round(chosen_test["accuracy_flagged"], 4),
        "test_accuracy_not_flagged": round(chosen_test["accuracy_not_flagged"], 4),
    }
    (directory / "review_margin.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nChuna gaya default margin: {margin} ({args.share:.0%} predictions review ke liye)")
    print(f"Save hua: {directory / 'review_margin.json'}")


if __name__ == "__main__":
    main()
