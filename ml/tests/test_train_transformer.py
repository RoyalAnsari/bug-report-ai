import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import train_transformer as tt  # noqa: E402


def test_class_weights_favour_rare_classes_and_average_to_one():
    counts = [7000, 100, 50, 10, 500, 20]
    weights = tt.class_weights(counts, power=0.5)
    assert weights.argmax() == counts.index(min(counts))
    assert weights.argmin() == counts.index(max(counts))
    assert weights.mean() == pytest.approx(1.0)


def test_class_weight_power_one_is_fully_balanced():
    counts = [100, 400]
    weights = tt.class_weights(counts, power=1.0)
    assert weights[0] / weights[1] == pytest.approx(4.0)


def test_class_weights_reject_an_empty_class():
    with pytest.raises(ValueError):
        tt.class_weights([10, 0, 5, 5, 5, 5])


def test_input_text_has_project_and_collapsed_spaces():
    assert tt.build_input_text("Crash   on\nsave", "Core Team") == "core_team: Crash on save"
    assert tt.build_input_text("x", None) == "unknown: x"


def test_tune_offsets_fixes_a_biased_class():
    rng = np.random.RandomState(0)
    y = rng.randint(0, 6, size=600)
    logits = rng.randn(600, 6) * 0.3
    logits[np.arange(600), y] += 1.0   # sahi class ka score zyada
    logits[:, 3] += 0.8                # lekin class 3 ki taraf jhukao
    before = tt.macro_f1(y, logits.argmax(axis=1))
    offsets, after = tt.tune_offsets(logits, y)
    assert after >= before
    assert offsets[3] < 0
