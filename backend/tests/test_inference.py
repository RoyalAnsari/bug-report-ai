import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.ml.inference import DuplicateFinder, SeverityPredictor, build_input_text


def test_build_input_text_without_project():
    assert build_input_text("  Crash   on start ", "Core", use_project=False) == "Crash on start"


def test_build_input_text_with_project():
    assert build_input_text("Crash", "Thunder bird", use_project=True) == "projthunder_bird Crash"
    assert build_input_text("Crash", None, use_project=True) == "projunknown Crash"


def make_predictor(review_margin=0.25):
    texts = (
        ["app crash on startup"] * 4
        + ["typo in help text"] * 4
        + ["button misaligned in dialog"] * 4
    )
    labels = ["blocker"] * 4 + ["trivial"] * 4 + ["normal"] * 4
    model = Pipeline([("tfidf", TfidfVectorizer()), ("svm", LinearSVC())])
    model.fit(texts, labels)
    classes = list(model.classes_)
    return SeverityPredictor(model, classes, np.zeros(len(classes)), False, review_margin)


def test_predict_returns_expected_structure():
    predictor = make_predictor()
    results = predictor.predict(["app crash on startup", "typo in help text"])
    assert len(results) == 2
    for item in results:
        assert item["label"] in predictor.classes
        assert item["margin"] >= 0
        assert isinstance(item["needs_review"], bool)
        assert set(item["scores"]) == set(predictor.classes)


def test_predict_empty_list_returns_empty():
    assert make_predictor().predict([]) == []


def test_predict_rejects_mismatched_projects():
    with pytest.raises(ValueError):
        make_predictor().predict(["one", "two"], projects=["Core"])


def test_review_flag_follows_margin():
    texts = ["app crash on startup", "typo in help text"]
    always = make_predictor(review_margin=1000.0).predict(texts)
    never = make_predictor(review_margin=0.0).predict(texts)
    assert all(item["needs_review"] for item in always)
    assert not any(item["needs_review"] for item in never)


class FakeEncoder:
    def __init__(self, mapping):
        self.mapping = mapping

    def encode(self, texts, **kwargs):
        return np.array([self.mapping[t] for t in texts], dtype=np.float32)


def make_finder():
    vectors = np.array([[1.0, 0.0], [0.9, 0.436], [0.0, 1.0]], dtype=np.float32)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    reports = pd.DataFrame(
        {
            "bug_id": [10, 20, 30],
            "project": ["Core", "Core", "JDT"],
            "text": ["crash on save", "crash when saving", "typo in menu"],
        }
    )
    encoder = FakeEncoder({"query": [1.0, 0.0]})
    return DuplicateFinder(encoder, vectors, reports, top_k=3, threshold=0.0)


def test_find_ranks_most_similar_first():
    hits = make_finder().find("query")
    assert [h["bug_id"] for h in hits] == [10, 20, 30]
    scores = [h["similarity"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_find_respects_threshold_and_top_k():
    finder = make_finder()
    assert [h["bug_id"] for h in finder.find("query", threshold=0.95)] == [10]
    assert len(finder.find("query", top_k=2)) == 2


def test_finder_rejects_mismatched_sizes():
    reports = pd.DataFrame({"bug_id": [1], "project": ["Core"], "text": ["a"]})
    with pytest.raises(ValueError):
        DuplicateFinder(FakeEncoder({}), np.zeros((2, 2)), reports)


def test_find_rejects_invalid_arguments():
    finder = make_finder()
    with pytest.raises(ValueError):
        finder.find("query", threshold=1.5)
    with pytest.raises(ValueError):
        finder.find("query", top_k=0)