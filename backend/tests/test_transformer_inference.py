import numpy as np
import pytest

from app.core.config import Settings
from app.ml.transformer_inference import (
    TransformerSeverityPredictor,
    build_input_text,
    softmax,
    version_from_model_name,
)
from app.repositories.model_versions import SEVERITY_NAME
from app.repositories.prediction_records import SEVERITY_MODEL_VERSION, build_prediction_document
from app.repositories.transformer_versions import build_transformer_document

LABELS = ["blocker", "critical", "major", "normal", "minor", "trivial"]


class StubPredictor(TransformerSeverityPredictor):
    """Asli model ke baghair: _logits ki jagah tay shuda numbers deta hai."""

    def __init__(self, logits, offsets=None, review_margin=0.2):
        super().__init__(None, None, LABELS, offsets or [0.0] * 6, review_margin, version="distilbert-base-uncased-v2")
        self.fixed = np.asarray(logits, dtype=np.float64)

    def _logits(self, inputs):
        assert len(inputs) == len(self.fixed)
        return self.fixed


def test_input_text_matches_the_training_format():
    assert build_input_text("Crash   on\nsave", "Core Team") == "core_team: Crash on save"
    assert build_input_text("x", None) == "unknown: x"


def test_softmax_rows_add_up_to_one():
    result = softmax(np.array([[1.0, 2.0, 3.0], [1000.0, 1000.0, 1000.0]]))
    assert np.allclose(result.sum(axis=1), 1.0)


def test_confident_prediction_is_not_flagged_and_close_call_is_flagged():
    predictor = StubPredictor([[0, 5, 0, 0, 0, 0], [0, 1.0, 0.9, 0, 0, 0]])
    sure, unsure = predictor.predict(["a", "b"], ["Core", "Core"])
    assert sure["label"] == "critical" and sure["needs_review"] is False and sure["margin"] > 0.9
    assert unsure["label"] == "critical" and unsure["needs_review"] is True and unsure["margin"] < 0.2


def test_result_has_the_same_fields_as_the_tfidf_predictor_plus_the_model_version():
    result = StubPredictor([[0, 0, 0, 3, 0, 0]]).predict(["x"])[0]
    assert set(result) == {"label", "margin", "needs_review", "scores", "model_version"}
    assert list(result["scores"]) == LABELS
    assert result["label"] == "normal"
    assert result["model_version"] == "distilbert-base-uncased-v2"


def test_offsets_can_change_the_winner():
    plain = StubPredictor([[0, 0, 0, 1.0, 0.8, 0]]).predict(["x"])[0]
    shifted = StubPredictor([[0, 0, 0, 1.0, 0.8, 0]], offsets=[0, 0, 0, 0, 0.5, 0]).predict(["x"])[0]
    assert plain["label"] == "normal" and shifted["label"] == "minor"


def test_empty_input_gives_an_empty_list_and_bad_projects_are_rejected():
    predictor = StubPredictor(np.zeros((0, 6)))
    assert predictor.predict([]) == []
    with pytest.raises(ValueError):
        StubPredictor([[0, 0, 0, 1, 0, 0]]).predict(["a"], ["Core", "JDT"])


def test_offsets_and_classes_must_match():
    with pytest.raises(ValueError):
        TransformerSeverityPredictor(None, None, LABELS, [0.0, 0.0])


def test_version_name_comes_from_the_model_name():
    assert version_from_model_name("distilbert-base-uncased") == "distilbert-base-uncased-v2"
    assert version_from_model_name("org/some-model") == "some-model-v2"


def test_prediction_record_keeps_the_model_version_of_the_result():
    transformer_result = StubPredictor([[0, 0, 0, 3, 0, 0]]).predict(["x"])[0]
    saved = build_prediction_document("br_1", transformer_result)
    assert saved["model_version"] == "distilbert-base-uncased-v2"

    tfidf_result = {"label": "major", "margin": 0.1, "needs_review": True, "scores": {"major": 1.0}}
    assert build_prediction_document("br_1", tfidf_result)["model_version"] == SEVERITY_MODEL_VERSION


def test_transformer_document_for_the_model_versions_page():
    metrics = {
        "chosen": {"variant": "transformer_distilbert-base-uncased", "offsets": True, "val_macro_f1": 0.4467},
        "test": {
            "macro_f1": 0.4491,
            "per_class": {
                label: {"precision": 0.5, "recall": 0.4, "f1-score": 0.45, "support": 10.0} for label in LABELS
            }
            | {"macro avg": {"precision": 0.49, "recall": 0.4, "f1-score": 0.45, "support": 60.0}},
            "confusion_matrix": [[1] * 6] * 6,
            "labels_order": LABELS,
            "rows": 60,
        },
        "training": {"model_name": "distilbert-base-uncased", "seed": 42},
        "versions": {"torch": "x"},
    }
    document = build_transformer_document(metrics)
    assert document["_id"] == f"{SEVERITY_NAME}:distilbert-base-uncased-v2"
    assert document["version"] == "distilbert-base-uncased-v2"
    assert document["evaluation"]["macro_f1"] == 0.4491
    assert document["evaluation"]["per_class"]["major"]["f1"] == 0.45
    assert document["training"]["validation_macro_f1"] == 0.4467


def test_settings_accept_only_known_severity_models_and_margins():
    Settings(severity_model="tfidf").validate_for_startup()
    Settings(severity_model="transformer", transformer_review_margin=0.3).validate_for_startup()
    with pytest.raises(ValueError):
        Settings(severity_model="gpt").validate_for_startup()
    with pytest.raises(ValueError):
        Settings(severity_model="transformer", transformer_review_margin=1.5).validate_for_startup()
