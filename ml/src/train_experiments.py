import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_data import LABELS, SEED  # noqa: E402
from train_baseline import print_summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACT_DIR = ROOT / "artifacts" / "severity_experiments"
RESAMPLE_TARGET = 5000


def make_text(df, use_project):
    """Model ke liye text banata hai. Optional: project ka naam shuru mein jod deta hai."""
    if not use_project:
        return df["text"]
    project = df["project"].astype(str).str.lower().str.replace(" ", "_")
    return "proj" + project + " " + df["text"]


def resample_train(df, target=None, seed=SEED):
    """Har class ko 'target' rows par laata hai (sirf train data ke liye)."""
    if target is None:
        return df
    parts = []
    for label in LABELS:
        part = df[df["severity"] == label]
        parts.append(part.sample(n=target, replace=len(part) < target, random_state=seed))
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


def build_model(use_char, class_weight):
    word = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=100000)
    steps = [("word", word)]
    if use_char:
        char = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=150000
        )
        steps.append(("char", char))
    return Pipeline(
        [
            ("features", FeatureUnion(steps)),
            ("svm", LinearSVC(class_weight=class_weight, C=1.0, max_iter=5000, random_state=SEED)),
        ]
    )


def macro_f1(y_true, y_pred):
    return float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0))


def predict_with_offsets(scores, offsets, classes):
    return classes[np.argmax(scores + offsets, axis=1)]


def fit_offsets(scores, y_true, classes):
    """Har class ka chhota adjustment dhoondta hai jo macro F1 barhaye."""
    y_true = np.asarray(y_true)
    offsets = np.zeros(len(classes))
    best = macro_f1(y_true, predict_with_offsets(scores, offsets, classes))
    for _ in range(3):
        for i in range(len(classes)):
            for value in np.arange(-1.0, 1.01, 0.1):
                trial = offsets.copy()
                trial[i] = value
                score = macro_f1(y_true, predict_with_offsets(scores, trial, classes))
                if score > best:
                    best, offsets = score, trial
    return offsets


def metrics_from_predictions(y_true, y_pred):
    return {
        "macro_f1": macro_f1(y_true, y_pred),
        "per_class": classification_report(
            y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
        "labels_order": LABELS,
        "rows": int(len(y_true)),
    }


VARIANTS = [
    {"name": "A_word_balanced", "project": False, "char": False, "resample": None, "cw": "balanced"},
    {"name": "B_word_project_balanced", "project": True, "char": False, "resample": None, "cw": "balanced"},
    {"name": "C_word_char_project_balanced", "project": True, "char": True, "resample": None, "cw": "balanced"},
    {"name": "D_word_char_project_resampled", "project": True, "char": True, "resample": RESAMPLE_TARGET, "cw": None},
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(PROCESSED_DIR / "train.csv", encoding="utf-8")
    val = pd.read_csv(PROCESSED_DIR / "val.csv", encoding="utf-8")
    test = pd.read_csv(PROCESSED_DIR / "test.csv", encoding="utf-8")
    val_a, val_b = train_test_split(val, test_size=0.5, stratify=val["severity"], random_state=SEED)

    results, trained = [], {}
    for variant in VARIANTS:
        print(f"Training: {variant['name']} ...")
        data = resample_train(train, variant["resample"])
        model = build_model(variant["char"], variant["cw"])
        model.fit(make_text(data, variant["project"]), data["severity"])
        classes = np.array(model.classes_)
        scores_a = model.decision_function(make_text(val_a, variant["project"]))
        scores_b = model.decision_function(make_text(val_b, variant["project"]))
        tuned = fit_offsets(scores_a, val_a["severity"], classes)
        trained[variant["name"]] = (model, classes, variant)
        for use_offsets in (False, True):
            offsets = tuned if use_offsets else np.zeros(len(classes))
            predictions = predict_with_offsets(scores_b, offsets, classes)
            results.append(
                {
                    "variant": variant["name"],
                    "offsets": use_offsets,
                    "val_macro_f1": macro_f1(val_b["severity"], predictions),
                    "offset_values": offsets.tolist(),
                }
            )

    print("\n=== Validation (doosra hissa) macro F1, behtar se kamzor ===")
    ranking = sorted(results, key=lambda r: r["val_macro_f1"], reverse=True)
    for r in ranking:
        print(f"{r['val_macro_f1']:.4f}  {r['variant']}  offsets={r['offsets']}")

    best = ranking[0]
    model, classes, variant = trained[best["variant"]]
    offsets = np.array(best["offset_values"])
    print(f"\nChuna gaya: {best['variant']} (offsets={best['offsets']})")

    scores_test = model.decision_function(make_text(test, variant["project"]))
    predictions = predict_with_offsets(scores_test, offsets, classes)
    test_metrics = metrics_from_predictions(test["severity"], predictions)
    print_summary("TEST (sirf ek baar chalaya)", test_metrics)

    joblib.dump(
        {
            "model": model,
            "classes": classes.tolist(),
            "offsets": offsets.tolist(),
            "use_project": variant["project"],
        },
        ARTIFACT_DIR / "model.joblib",
    )
    output = {
        "chosen": best,
        "all_validation_results": results,
        "test": test_metrics,
        "resample_target": RESAMPLE_TARGET,
        "seed": SEED,
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("\nSaved:", ARTIFACT_DIR)


if __name__ == "__main__":
    main()