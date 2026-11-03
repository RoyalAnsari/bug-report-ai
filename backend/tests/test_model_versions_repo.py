from app.repositories.model_versions import (
    build_duplicate_document,
    build_severity_document,
    extract_evaluation,
    to_summary,
)
from app.repositories.prediction_records import SEVERITY_MODEL_VERSION

# Yeh sirf test ke liye banaye hue chhote numbers hain, asli metrics nahi
METRICS = {
    "chosen": {"variant": "C_word_char_project_balanced", "offsets": True, "val_macro_f1": 0.5},
    "test": {
        "macro_f1": 0.6,
        "per_class": {
            "blocker": {"precision": 0.7, "recall": 0.3, "f1-score": 0.4, "support": 10.0},
            "major": {"precision": 0.2, "recall": 0.1, "f1-score": 0.1, "support": 20.0},
            "accuracy": 0.8,
            "macro avg": {"precision": 0.45, "recall": 0.2, "f1-score": 0.25, "support": 30.0},
            "weighted avg": {"precision": 0.3, "recall": 0.1, "f1-score": 0.2, "support": 30.0},
        },
        "confusion_matrix": [[3, 7], [18, 2]],
        "labels_order": ["blocker", "major"],
        "rows": 30,
    },
    "seed": 42,
    "resample_target": 5000,
    "versions": {"python": "3.14", "scikit_learn": "1.9"},
}

CONFIG = {"model": "sentence-transformers/all-MiniLM-L6-v2", "rows": 5, "default_threshold": 0.8}


def test_extract_evaluation_keeps_only_label_rows():
    evaluation = extract_evaluation(METRICS["test"])
    assert set(evaluation["per_class"]) == {"blocker", "major"}
    assert evaluation["per_class"]["blocker"] == {
        "precision": 0.7, "recall": 0.3, "f1": 0.4, "support": 10,
    }


def test_extract_evaluation_includes_macro_values_and_matrix():
    evaluation = extract_evaluation(METRICS["test"])
    assert evaluation["macro_f1"] == 0.6
    assert evaluation["macro_precision"] == 0.45
    assert evaluation["macro_recall"] == 0.2
    assert evaluation["confusion_matrix"] == [[3, 7], [18, 2]]
    assert evaluation["labels_order"] == ["blocker", "major"]


def test_severity_document_uses_prediction_version_and_chosen_variant():
    doc = build_severity_document(METRICS)
    assert doc["version"] == SEVERITY_MODEL_VERSION
    assert doc["_id"] == f"severity-classifier:{SEVERITY_MODEL_VERSION}"
    assert doc["variant"] == "C_word_char_project_balanced"
    assert doc["uses_offsets"] is True
    assert doc["evaluation"]["split"] == "test"
    assert doc["training"]["validation_macro_f1"] == 0.5


def test_duplicate_document_has_no_invented_metrics():
    doc = build_duplicate_document(CONFIG)
    assert doc["evaluation"] is None
    assert "not measured" in doc["evaluation_note"]
    assert doc["config"]["default_threshold"] == 0.8
    assert doc["config"]["embedding_dim"] is None  # jo config mein nahi, wo bana nahi


def test_summary_with_evaluation():
    summary = to_summary(build_severity_document(METRICS))
    assert summary["has_evaluation"] is True
    assert summary["macro_f1"] == 0.6


def test_summary_without_evaluation():
    summary = to_summary(build_duplicate_document(CONFIG))
    assert summary["has_evaluation"] is False
    assert summary["macro_f1"] is None