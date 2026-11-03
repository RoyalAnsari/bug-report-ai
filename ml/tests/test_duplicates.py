import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duplicates import normalize_rows, top_k_similar  # noqa: E402


def make_corpus():
    return normalize_rows(
        [
            [1.0, 0.0],   # 0
            [0.9, 0.1],   # 1: 0 ke bohat qareeb
            [0.0, 1.0],   # 2: bilkul alag
            [0.7, 0.7],   # 3: darmiyan mein
        ]
    )


def test_normalize_rows_gives_unit_length():
    result = normalize_rows([[3.0, 4.0], [0.0, 0.0]])
    assert np.isclose(np.linalg.norm(result[0]), 1.0)
    assert np.allclose(result[1], [0.0, 0.0])


def test_top_k_returns_most_similar_first():
    corpus = make_corpus()
    result = top_k_similar(corpus[[0]], corpus, k=3, query_indices=[0])
    indices = [i for i, _ in result[0]]
    scores = [s for _, s in result[0]]
    assert indices[0] == 1
    assert scores == sorted(scores, reverse=True)


def test_query_does_not_match_itself():
    corpus = make_corpus()
    result = top_k_similar(corpus[[2]], corpus, k=4, query_indices=[2])
    assert 2 not in [i for i, _ in result[0]]


def test_threshold_filters_low_scores():
    corpus = make_corpus()
    result = top_k_similar(corpus[[0]], corpus, k=3, threshold=0.95, query_indices=[0])
    assert [i for i, _ in result[0]] == [1]


def test_k_larger_than_corpus_is_safe():
    corpus = make_corpus()
    result = top_k_similar(corpus[[0]], corpus, k=50, query_indices=[0])
    assert len(result[0]) == 3