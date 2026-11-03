import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prepare_data import LABELS, clean_dataframe, clean_text, split_dataframe  # noqa: E402

RAW_COLUMNS = ["Project", "Bug ID", "Severity Label", "Resolution Status", "Short Description"]


def make_raw(rows):
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def test_clean_text_collapses_whitespace():
    assert clean_text("  Crash   on\tstart\n ") == "Crash on start"


def test_clean_text_handles_non_string():
    assert clean_text(float("nan")) == ""
    assert clean_text(None) == ""


def test_removes_duplicate_bug_id():
    raw = make_raw([
        ["Core", 1, "major", "FIXED", "First text"],
        ["Core", 1, "major", "FIXED", "Another text"],
    ])
    clean, report = clean_dataframe(raw)
    assert len(clean) == 1
    assert report["removed_duplicate_bug_id"] == 1


def test_removes_unknown_label_and_empty_text():
    raw = make_raw([
        ["Core", 1, "enhancement", "FIXED", "Some text"],
        ["Core", 2, "major", "FIXED", "   "],
        ["Core", 3, "minor", "FIXED", "Good report"],
    ])
    clean, _ = clean_dataframe(raw)
    assert clean["bug_id"].tolist() == [3]


def test_removes_same_text_with_conflicting_labels():
    raw = make_raw([
        ["Core", 1, "major", "FIXED", "Crash"],
        ["Core", 2, "minor", "FIXED", "crash"],
        ["Core", 3, "normal", "FIXED", "Different report"],
    ])
    clean, report = clean_dataframe(raw)
    assert clean["bug_id"].tolist() == [3]
    assert report["removed_same_text_conflicting_label"] == 2


def test_keeps_one_row_for_same_text_same_label():
    raw = make_raw([
        ["Core", 1, "major", "FIXED", "Crash on save"],
        ["Core", 2, "major", "FIXED", "Crash on save"],
    ])
    clean, _ = clean_dataframe(raw)
    assert len(clean) == 1


def make_balanced_frame(per_class=20):
    rows = []
    bug_id = 0
    for label in LABELS:
        for i in range(per_class):
            bug_id += 1
            rows.append(["Core", bug_id, label, "FIXED", f"report {label} number {i}"])
    clean, _ = clean_dataframe(make_raw(rows))
    return clean


def test_split_has_no_overlap_and_keeps_all_rows():
    df = make_balanced_frame()
    train, val, test = split_dataframe(df)
    assert len(train) + len(val) + len(test) == len(df)
    ids = [set(part["bug_id"]) for part in (train, val, test)]
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])
    texts = [set(part["text"].str.lower()) for part in (train, val, test)]
    assert not (texts[0] & texts[1]) and not (texts[0] & texts[2])


def test_split_keeps_every_class_in_every_part():
    train, val, test = split_dataframe(make_balanced_frame())
    for part in (train, val, test):
        assert set(part["severity"]) == set(LABELS)


def test_split_is_reproducible():
    df = make_balanced_frame()
    first = split_dataframe(df, seed=42)[0]["bug_id"].tolist()
    second = split_dataframe(df, seed=42)[0]["bug_id"].tolist()
    assert first == second