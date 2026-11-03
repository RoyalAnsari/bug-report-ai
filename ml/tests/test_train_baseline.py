import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prepare_data import LABELS  # noqa: E402
from train_baseline import build_pipeline, evaluate  # noqa: E402


def make_tiny_frame():
    topics = {
        "blocker": "application crash on startup",
        "critical": "data loss when saving file",
        "major": "feature does not work correctly",
        "normal": "button label is misaligned",
        "minor": "small cosmetic issue in dialog",
        "trivial": "typo in help text",
    }
    rows = []
    for label, text in topics.items():
        for i in range(10):
            rows.append({"text": f"{text} case {i}", "severity": label})
    return pd.DataFrame(rows)


def test_pipeline_fits_and_predicts_known_labels():
    df = make_tiny_frame()
    model = build_pipeline("balanced")
    model.fit(df["text"], df["severity"])
    predictions = model.predict(df["text"])
    assert set(predictions).issubset(set(LABELS))
    assert len(predictions) == len(df)


def test_balanced_option_is_applied():
    assert build_pipeline("balanced").named_steps["svm"].class_weight == "balanced"
    assert build_pipeline(None).named_steps["svm"].class_weight is None


def test_evaluate_returns_expected_structure():
    df = make_tiny_frame()
    model = build_pipeline("balanced").fit(df["text"], df["severity"])
    metrics = evaluate(model, df)
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    matrix = metrics["confusion_matrix"]
    assert len(matrix) == len(LABELS) and all(len(row) == len(LABELS) for row in matrix)
    assert sum(sum(row) for row in matrix) == len(df)
    for label in LABELS:
        assert "precision" in metrics["per_class"][label]
        assert "recall" in metrics["per_class"][label]
        