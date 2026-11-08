"""TF-IDF aur transformer ke scores milakar dekhta hai ke nateeja behtar hota hai ya nahi, aur farq asli hai ya ittefaq.

Yeh laptop (CPU) par chalta hai, GPU nahi chahiye. Pehle Colab ki output zip (severity_transformer.zip) ko
ml/artifacts/severity_transformer mein extract karein (is mein val_logits.npy, test_logits.npy wagaira hain).

Tareeqa (insaaf ke liye):
  - dono models ke scores ko validation ke hisaab se ek paimane par laate hain,
  - milane ka weight aur har class ka offset sirf VALIDATION par chunte hain,
  - test sirf aakhir mein ek baar naapte hain,
  - "farq asli hai ya ittefaq" ke liye paired bootstrap (test ke rows ko 1000 baar dobara chunna).

Chalane ka tareeqa (repo ke root se, venv active):
  python ml/src/ensemble_eval.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_transformer as tt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LABELS = tt.LABELS


def tfidf_input(text, project, use_project):
    """Bilkul wahi jo backend/app/ml/inference.py ka build_input_text karta hai."""
    text = " ".join(str(text).split())
    if not use_project:
        return text
    name = str(project or "unknown").strip().lower().replace(" ", "_")
    return f"proj{name} {text}"


def read_split(data_dir, name):
    frame = pd.read_csv(Path(data_dir) / f"{name}.csv", encoding="utf-8")
    mapping = {label: index for index, label in enumerate(LABELS)}
    return frame["text"], frame["project"], frame["severity"].map(mapping).to_numpy(dtype=np.int64)


def tfidf_scores(artifact, texts, projects):
    classes = list(artifact["classes"])
    if set(classes) != set(LABELS):
        raise SystemExit(f"TF-IDF model ki classes alag hain: {classes}")
    order = [classes.index(label) for label in LABELS]  # LABELS ki tarteeb mein
    inputs = [tfidf_input(t, p, artifact["use_project"]) for t, p in zip(texts, projects)]
    scores = np.asarray(artifact["model"].decision_function(inputs), dtype=np.float64)[:, order]
    offsets = np.asarray(artifact["offsets"], dtype=np.float64)[order]
    return scores, offsets


def standardise(scores, reference):
    return (scores - reference.mean()) / reference.std()


def describe(name, y, pred):
    from sklearn.metrics import accuracy_score, f1_score

    per_class = f1_score(y, pred, labels=list(range(len(LABELS))), average=None, zero_division=0)
    print(f"{name:22s} macro F1 {tt.macro_f1(y, pred):.4f}   accuracy {accuracy_score(y, pred):.4f}   "
          + "  ".join(f"{label[:4]} {value:.2f}" for label, value in zip(LABELS, per_class)))


def paired_bootstrap(y, pred_a, pred_b, rounds=1000, seed=42):
    rng = np.random.RandomState(seed)
    diffs = np.empty(rounds)
    for i in range(rounds):
        idx = rng.randint(0, len(y), size=len(y))
        diffs[i] = tt.macro_f1(y[idx], pred_b[idx]) - tt.macro_f1(y[idx], pred_a[idx])
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(diffs.mean()), float(low), float(high)


def verdict(low, high):
    if low > 0:
        return "daira 0 se upar hai: farq asli lagta hai"
    if high < 0:
        return "daira 0 se neeche hai: yeh model sach mein kharab hai"
    return "daira 0 ko shamil karta hai: farq ittefaq ho sakta hai"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(ROOT / "ml" / "data" / "processed"))
    parser.add_argument("--transformer-dir", default=str(ROOT / "ml" / "artifacts" / "severity_transformer"))
    parser.add_argument("--tfidf-dir", default=str(ROOT / "ml" / "artifacts" / "severity_experiments"))
    parser.add_argument("--out-dir", default=str(ROOT / "ml" / "artifacts" / "severity_ensemble"))
    args = parser.parse_args()

    import joblib

    transformer_dir = Path(args.transformer_dir)
    needed = ["val_logits.npy", "test_logits.npy", "val_labels.npy", "test_labels.npy", "offsets.json"]
    absent = [name for name in needed if not (transformer_dir / name).exists()]
    if absent:
        raise SystemExit(f"{transformer_dir} mein yeh files nahi hain: {absent}. Colab ki zip yahan extract karein.")

    artifact = joblib.load(Path(args.tfidf_dir) / "model.joblib")
    val_text, val_project, y_val = read_split(args.data_dir, "val")
    test_text, test_project, y_test = read_split(args.data_dir, "test")

    # Dono models ke rows ek hi tarteeb mein hone chahiye.
    if not np.array_equal(y_val, np.load(transformer_dir / "val_labels.npy")) or not np.array_equal(
        y_test, np.load(transformer_dir / "test_labels.npy")
    ):
        raise SystemExit("Transformer ke labels CSV se mel nahi khate (shayad Colab par --limit use hua tha, ya files badal gayi hain).")

    tf_val, tf_offsets = tfidf_scores(artifact, val_text, val_project)
    tf_test, _ = tfidf_scores(artifact, test_text, test_project)
    tr_val = np.load(transformer_dir / "val_logits.npy").astype(np.float64)
    tr_test = np.load(transformer_dir / "test_logits.npy").astype(np.float64)
    tr_offsets = np.asarray(json.loads((transformer_dir / "offsets.json").read_text()), dtype=np.float64)

    pred_tfidf = (tf_test + tf_offsets).argmax(axis=1)
    pred_transformer = (tr_test + tr_offsets).argmax(axis=1)

    # Jaanch: TF-IDF ka test F1 wahi aana chahiye jo metrics.json mein hai.
    metrics_path = Path(args.tfidf_dir) / "metrics.json"
    if metrics_path.exists():
        recorded = json.loads(metrics_path.read_text(encoding="utf-8"))["test"]["macro_f1"]
        ours = tt.macro_f1(y_test, pred_tfidf)
        note = "theek" if abs(ours - recorded) < 0.002 else "MEL NAHI KHATA, nateeje par bharosa na karein"
        print(f"Jaanch: TF-IDF test macro F1 yahan {ours:.4f}, metrics.json mein {recorded:.4f} ({note})\n")

    # Milana: dono ko validation ke hisaab se ek paimane par laakar weight chunna.
    tf_val_z, tf_test_z = standardise(tf_val, tf_val), standardise(tf_test, tf_val)
    tr_val_z, tr_test_z = standardise(tr_val, tr_val), standardise(tr_test, tr_val)
    best = None
    print("TF-IDF ka weight    validation macro F1 (offsets ke saath)")
    for weight in [round(0.1 * step, 1) for step in range(11)]:
        combined = weight * tf_val_z + (1 - weight) * tr_val_z
        offsets, score = tt.tune_offsets(combined, y_val)
        print(f"   {weight:.1f}                {score:.4f}")
        if best is None or score > best[0]:
            best = (score, weight, offsets)
    val_score, weight, offsets = best
    pred_ensemble = (weight * tf_test_z + (1 - weight) * tr_test_z + offsets).argmax(axis=1)
    print(f"\nChuna gaya weight: TF-IDF {weight:.1f}, transformer {1 - weight:.1f} (validation macro F1 {val_score:.4f})\n")

    print("TEST (aakhri mukabla, sirf ek baar):")
    describe("TF-IDF", y_test, pred_tfidf)
    describe("Transformer", y_test, pred_transformer)
    describe("Milana (ensemble)", y_test, pred_ensemble)

    print("\nFarq asli hai ya ittefaq? (test macro F1 ka farq, 1000 baar dobara chun kar, 95% daira)")
    results = {}
    for label, pred in (("Transformer - TF-IDF", pred_transformer), ("Ensemble - TF-IDF", pred_ensemble)):
        mean, low, high = paired_bootstrap(y_test, pred_tfidf, pred)
        results[label] = {"mean_difference": round(mean, 4), "interval": [round(low, 4), round(high, 4)]}
        print(f"  {label:22s} {mean:+.4f}   [{low:+.4f}, {high:+.4f}]   {verdict(low, high)}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps(
            {
                "tfidf_weight": weight,
                "offsets": [float(x) for x in offsets],
                "labels_order": LABELS,
                "standardisation": {
                    "tfidf": {"mean": float(tf_val.mean()), "std": float(tf_val.std())},
                    "transformer": {"mean": float(tr_val.mean()), "std": float(tr_val.std())},
                },
                "validation_macro_f1": val_score,
                "test_macro_f1": {
                    "tfidf": tt.macro_f1(y_test, pred_tfidf),
                    "transformer": tt.macro_f1(y_test, pred_transformer),
                    "ensemble": tt.macro_f1(y_test, pred_ensemble),
                },
                "paired_bootstrap": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSave hua: {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
