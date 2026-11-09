"""Backend ko chalane ke liye zaroori model files maujood hain ya nahi, yeh dekhta hai.

Agar maujood na hon aur MODELS_REPO set ho, to unhein Hugging Face ke repo se download karta hai.
Private repo ke liye HF_TOKEN chahiye. Model files Git mein nahi hoti (bohat bari hain).
"""
import os
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"

REQUIRED = [
    "severity_experiments/model.joblib",
    "duplicates/config.json",
    "duplicates/embeddings.npy",
    "duplicates/reports_index.csv",
    "models/all-MiniLM-L6-v2/modules.json",
]
WEIGHT_FILES = ["model.safetensors", "pytorch_model.bin"]

# Sirf tab zaroori jab SEVERITY_MODEL=transformer ho.
TRANSFORMER_REQUIRED = [
    "severity_transformer/labels.json",
    "severity_transformer/offsets.json",
    "severity_transformer/model/config.json",
    "severity_transformer/model/model.safetensors",
]


def missing_files(root, transformer=False):
    root = Path(root)
    required = REQUIRED + (TRANSFORMER_REQUIRED if transformer else [])
    missing = [name for name in required if not (root / name).is_file()]
    model_dir = root / "models" / "all-MiniLM-L6-v2"
    if not any((model_dir / name).is_file() for name in WEIGHT_FILES):
        missing.append("models/all-MiniLM-L6-v2/model.safetensors")
    return missing


def main():
    if os.getenv("LOAD_MODELS", "true").strip().lower() == "false":
        print("LOAD_MODELS=false: models ki jaanch chhodi ja rahi hai.")
        return 0

    root = Path(os.getenv("ARTIFACTS_DIR") or DEFAULT_DIR)
    transformer = os.getenv("SEVERITY_MODEL", "tfidf").strip().lower() == "transformer"
    missing = missing_files(root, transformer)
    if not missing:
        print(f"Models maujood hain: {root}")
        return 0

    repo = os.getenv("MODELS_REPO", "").strip()
    if not repo:
        print("Yeh model files nahi milin:")
        for name in missing:
            print(f"  {name}")
        print("Unhein {} mein rakhein (mount karke), ya MODELS_REPO set karein taake woh download ho jayen.".format(root))
        return 1

    print(f"Models download ho rahe hain: {repo}")
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo,
        repo_type="model",
        local_dir=str(root),
        token=os.getenv("HF_TOKEN") or None,
    )

    missing = missing_files(root, transformer)
    if missing:
        print("Download ke baad bhi yeh files nahi milin:")
        for name in missing:
            print(f"  {name}")
        return 1
    print("Models tayyar hain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
