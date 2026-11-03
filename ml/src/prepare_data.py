import json
import re
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "bugzilla_eclipse" / "filtered_data.xlsx - Sheet1.csv"
OUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

# Labels hamne dataset inspect karke liye hain (severity ke order mein)
LABELS = ["blocker", "critical", "major", "normal", "minor", "trivial"]
COLUMN_MAP = {
    "Project": "project",
    "Bug ID": "bug_id",
    "Severity Label": "severity",
    "Short Description": "text",
}
SEED = 42
MIN_TEXT_LENGTH = 3


def clean_text(value):
    """Control characters hatata hai aur extra spaces ek kar deta hai."""
    if not isinstance(value, str):
        return ""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def clean_dataframe(df):
    """Raw data saaf karta hai. (saaf data, report dictionary) wapas deta hai."""
    report = {"rows_start": len(df)}
    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())].copy()
    df["severity"] = df["severity"].astype(str).str.strip().str.lower()
    df["text"] = df["text"].map(clean_text)

    before = len(df)
    df = df[df["severity"].isin(LABELS)]
    report["removed_unknown_label"] = before - len(df)

    before = len(df)
    df = df[df["text"].str.len() >= MIN_TEXT_LENGTH]
    report["removed_short_or_empty_text"] = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset="bug_id", keep="first")
    report["removed_duplicate_bug_id"] = before - len(df)

    # Same text par alag alag labels ho to wo rows confusing hain, hata dete hain
    df = df.assign(_key=df["text"].str.lower())
    label_count = df.groupby("_key")["severity"].transform("nunique")
    before = len(df)
    df = df[label_count == 1]
    report["removed_same_text_conflicting_label"] = before - len(df)

    # Same text aur same label ho to sirf ek row rakhte hain
    before = len(df)
    df = df.drop_duplicates(subset="_key", keep="first")
    report["removed_same_text_same_label"] = before - len(df)

    df = df.drop(columns="_key").reset_index(drop=True)
    report["rows_end"] = len(df)
    return df, report


def split_dataframe(df, seed=SEED):
    """80% train, 10% validation, 10% test. Har split mein class ka ratio barabar."""
    train, temp = train_test_split(
        df, test_size=0.2, stratify=df["severity"], random_state=seed
    )
    val, test = train_test_split(
        temp, test_size=0.5, stratify=temp["severity"], random_state=seed
    )
    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(RAW_CSV, encoding="utf-8")
    clean, report = clean_dataframe(raw)
    train, val, test = split_dataframe(clean)

    for name, part in (("train", train), ("val", val), ("test", test)):
        part.to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8")

    label_mapping = {label: index for index, label in enumerate(LABELS)}
    (OUT_DIR / "label_mapping.json").write_text(
        json.dumps(label_mapping, indent=2), encoding="utf-8"
    )

    report["seed"] = SEED
    report["split_sizes"] = {"train": len(train), "val": len(val), "test": len(test)}
    report["class_counts"] = {
        name: part["severity"].value_counts().to_dict()
        for name, part in (("train", train), ("val", val), ("test", test))
    }
    (REPORT_DIR / "prepare_data_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()