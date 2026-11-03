import sys
from pathlib import Path

import pandas as pd

# Windows terminal mein har tarah ka text print ho sake
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "bugzilla_eclipse" / "filtered_data.xlsx - Sheet1.csv"


def load_csv(path):
    """CSV ko alag alag encoding se padhne ki koshish karta hai."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError("CSV ko kisi encoding se nahi padh saka")


df, encoding = load_csv(CSV_PATH)

print("File:", CSV_PATH.name)
print("Encoding:", encoding)
print("Rows, Columns:", df.shape)

print("\n=== Columns, type, missing values, unique values ===")
summary = pd.DataFrame(
    {
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    }
)
print(summary.to_string())

print("\n=== Value counts (sirf un columns ke jin mein 15 ya kam unique values hain) ===")
for column in df.columns:
    if df[column].nunique(dropna=True) <= 15:
        print(f"\n--- {column} ---")
        print(df[column].value_counts(dropna=False).to_string())

print("\n=== Duplicate rows (bilkul same poori row) ===")
print(df.duplicated().sum())

print("\n=== Pehli 3 rows (text 100 characters par kata hua) ===")
sample = df.head(3).astype(str).apply(lambda col: col.str.slice(0, 100))
print(sample.T.to_string())