import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duplicates import top_k_similar  # noqa: E402
from prepare_data import SEED  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "artifacts" / "models" / "all-MiniLM-L6-v2"
OUT_DIR = ROOT / "artifacts" / "duplicates"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_all_reports(limit=None):
    frames = [
        pd.read_csv(PROCESSED_DIR / f"{name}.csv", encoding="utf-8")
        for name in ("train", "val", "test")
    ]
    df = pd.concat(frames, ignore_index=True)
    if limit:
        df = df.sample(n=min(limit, len(df)), random_state=SEED).reset_index(drop=True)
    return df


def short(text, size=90):
    text = str(text)
    return text if len(text) <= size else text[: size - 3] + "..."


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="sirf itni reports lo (tez test ke liye)")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.80)
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_all_reports(args.limit)
    print("Reports:", len(df))

    model = SentenceTransformer(str(MODEL_DIR), device="cpu")
    started = time.time()
    embeddings = model.encode(
        df["text"].tolist(),
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)
    seconds = round(time.time() - started, 1)
    print("Embeddings shape:", embeddings.shape, "| time (seconds):", seconds)

    np.save(OUT_DIR / "embeddings.npy", embeddings)
    df[["bug_id", "project", "severity", "text"]].to_csv(
        OUT_DIR / "reports_index.csv", index=False, encoding="utf-8"
    )
    config = {
        "model": MODEL_NAME,
        "rows": int(len(df)),
        "embedding_dim": int(embeddings.shape[1]),
        "normalized": True,
        "score_type": "cosine similarity (not a probability)",
        "batch_size": args.batch_size,
        "default_top_k": args.top_k,
        "default_threshold": args.threshold,
        "encode_seconds": seconds,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
    }
    (OUT_DIR / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    rng = np.random.default_rng(SEED)
    sample = rng.choice(len(df), size=min(1000, len(df)), replace=False)
    results = top_k_similar(
        embeddings[sample], embeddings, k=args.top_k, threshold=args.threshold, query_indices=sample
    )
    with_candidate = sum(1 for r in results if r)
    print(
        f"\n{len(sample)} random reports mein se {with_candidate} ke liye "
        f"similarity >= {args.threshold} wale candidates mile."
    )

    print("\n=== 3 misaalein (similarity = cosine similarity, probability nahi) ===")
    for position in range(3):
        index = int(sample[position])
        print(f"\nReport {df.loc[index, 'bug_id']}: {short(df.loc[index, 'text'])}")
        candidates = top_k_similar(
            embeddings[[index]], embeddings, k=args.top_k, threshold=0.0, query_indices=[index]
        )[0]
        for other, score in candidates:
            print(f"   {score:.3f}  [{df.loc[other, 'bug_id']}] {short(df.loc[other, 'text'])}")

    print("\nSaved:", OUT_DIR)


if __name__ == "__main__":
    main()