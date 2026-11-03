import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prepare_data import LABELS  # noqa: E402
from train_experiments import (  # noqa: E402
    fit_offsets,
    macro_f1,
    make_text,
    predict_with_offsets,
    resample_train,
)


def make_unbalanced_frame():
    counts = {"blocker": 3, "critical": 8, "major": 12, "normal": 200, "minor": 10, "trivial": 5}
    rows = []
    for label, count in counts.items():
        for i in range(count):
            rows.append({"project": "Core", "text": f"{label} report {i}", "severity": label})
    return pd.DataFrame(rows)


def test_resample_gives_equal_class_counts():
    result = resample_train(make_unbalanced_frame(), target=20)
    counts = result["severity"].value_counts()
    assert set(counts.index) == set(LABELS)
    assert (counts == 20).all()


def test_resample_none_keeps_data_unchanged():
    df = make_unbalanced_frame()
    assert len(resample_train(df, target=None)) == len(df)


def test_make_text_adds_project_token():
    df = pd.DataFrame({"project": ["Core", "Firefox"], "text": ["crash", "typo"]})
    assert make_text(df, use_project=False).tolist() == ["crash", "typo"]
    assert make_text(df, use_project=True).tolist() == ["projcore crash", "projfirefox typo"]


def test_fit_offsets_is_never_worse_than_no_offsets():
    rng = np.random.default_rng(0)
    classes = np.array(sorted(LABELS))
    scores = rng.normal(size=(120, len(classes)))
    y_true = classes[np.argmax(scores, axis=1)]
    scores[:, list(classes).index("normal")] += 0.8  # model ko normal ki taraf jhuka dete hain
    base = macro_f1(y_true, predict_with_offsets(scores, np.zeros(len(classes)), classes))
    offsets = fit_offsets(scores, y_true, classes)
    tuned = macro_f1(y_true, predict_with_offsets(scores, offsets, classes))
    assert tuned >= base