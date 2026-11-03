import json
import platform
import sys
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_data import LABELS, SEED  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACT_DIR = ROOT / "artifacts" / "severity_baseline"

TFIDF_CONFIG = {"ngram_range": [1, 2], "min_df": 2, "sublinear_tf": True, "max_features": 100000}
SVM_CONFIG = {"C": 1.0, "max_iter": 5000}


def build_pipeline(class_weight=None):
    """TF-IDF + LinearSVC pipeline banata hai."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=tuple(TFIDF_CONFIG["ngram_range"]),
                    min_df=TFIDF_CONFIG["min_df"],
                    sublinear_tf=TFIDF_CONFIG["sublinear_tf"],
                    max_features=TFIDF_CONFIG["max_features"],
                ),
            ),
            (
                "svm",
                LinearSVC(
                    class_weight=class_weight,
                    C=SVM_CONFIG["C"],
                    max_iter=SVM_CONFIG["max_iter"],
                    random_state=SEED,
                ),
            ),
        ]
    )


def evaluate(model, df):
    """Macro F1, har class ka precision/recall aur confusion matrix wapas deta hai."""
    y_true = df["severity"]
    y_pred = model.predict(df["text"])
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "per_class": classification_report(
            y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
        "labels_order": LABELS,
        "rows": int(len(df)),
    }


def print_summary(title, metrics):
    print(f"\n=== {title} ===")
    print("Macro F1:", round(metrics["macro_f1"], 4))
    table = pd.DataFrame(metrics["per_class"]).T.loc[LABELS, ["precision", "recall", "f1-score", "support"]]
    print(table.round(3).to_string())
    print("\nConfusion matrix (rows = asli label, columns = predicted label):")
    print(pd.DataFrame(metrics["confusion_matrix"], index=LABELS, columns=LABELS).to_string())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(PROCESSED_DIR / "train.csv", encoding="utf-8")
    val = pd.read_csv(PROCESSED_DIR / "val.csv", encoding="utf-8")
    test = pd.read_csv(PROCESSED_DIR / "test.csv", encoding="utf-8")

    variants = {"no_balancing": None, "class_weight_balanced": "balanced"}
    models, val_results = {}, {}
    for name, class_weight in variants.items():
        print(f"Training: {name} ...")
        model = build_pipeline(class_weight)
        model.fit(train["text"], train["severity"])
        models[name] = model
        val_results[name] = evaluate(model, val)
        print_summary(f"VALIDATION - {name}", val_results[name])

    best = max(val_results, key=lambda n: val_results[n]["macro_f1"])
    print(f"\nValidation macro F1 ke hisab se chuna gaya: {best}")

    test_metrics = evaluate(models[best], test)
    print_summary(f"TEST - {best} (sirf ek baar chalaya)", test_metrics)

    joblib.dump(models[best], ARTIFACT_DIR / "model.joblib")
    result = {
        "model": "TF-IDF + LinearSVC",
        "chosen_variant": best,
        "seed": SEED,
        "tfidf_config": TFIDF_CONFIG,
        "svm_config": SVM_CONFIG,
        "train_rows": int(len(train)),
        "validation": val_results,
        "test": test_metrics,
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("\nSaved:", ARTIFACT_DIR)


if __name__ == "__main__":
    main()