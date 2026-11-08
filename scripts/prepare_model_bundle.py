"""Backend ko chalane ke liye zaroori model files ek chhote folder (model_bundle) mein jama karta hai.

ml/artifacts bohat bara hai (MiniLM ke onnx, openvino aur dusre framework ki copies bhi hain).
Backend ko in mein se sirf thori files chahiye. Chalane ka tareeqa (repo ke root se):
    python scripts/prepare_model_bundle.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ml" / "artifacts"
TARGET = ROOT / "model_bundle"

MINILM = "models/all-MiniLM-L6-v2"
SKIP_DIRS = {"onnx", "openvino", ".cache", "__pycache__"}
SKIP_FILES = {"tf_model.h5", "rust_model.ot", "flax_model.msgpack", "train_script.py"}

# backend/fetch_models.py ke REQUIRED jaisi hi files.
REQUIRED = [
    "severity_experiments/model.joblib",
    "duplicates/config.json",
    "duplicates/embeddings.npy",
    "duplicates/reports_index.csv",
    f"{MINILM}/modules.json",
]


def copy_plain_folder(name):
    source = SOURCE / name
    if not source.is_dir():
        raise FileNotFoundError(f"ml/artifacts/{name} nahi mila")
    shutil.copytree(source, TARGET / name, ignore=shutil.ignore_patterns("__pycache__", ".cache"))


def copy_minilm():
    source = SOURCE / MINILM
    if not source.is_dir():
        raise FileNotFoundError(f"ml/artifacts/{MINILM} nahi mila")
    has_safetensors = (source / "model.safetensors").is_file()
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        if path.name == "pytorch_model.bin" and has_safetensors:
            continue
        destination = TARGET / MINILM / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def copy_transformer():
    """Transformer ki zaroori files (model, labels, offsets, metrics, review margin). Logits wagaira nahi."""
    source = SOURCE / "severity_transformer"
    if not (source / "model").is_dir():
        return False
    shutil.copytree(source / "model", TARGET / "severity_transformer" / "model")
    for name in ("labels.json", "offsets.json", "metrics.json", "review_margin.json"):
        if (source / name).is_file():
            shutil.copy2(source / name, TARGET / "severity_transformer" / name)
    return True


def folder_size_mb(folder):
    return sum(item.stat().st_size for item in folder.rglob("*") if item.is_file()) / (1024 * 1024)


TRANSFORMER_REQUIRED = [
    "severity_transformer/labels.json",
    "severity_transformer/offsets.json",
    "severity_transformer/model/config.json",
    "severity_transformer/model/model.safetensors",
]


def verify():
    required = REQUIRED + (TRANSFORMER_REQUIRED if (TARGET / "severity_transformer").is_dir() else [])
    problems = [name for name in required if not (TARGET / name).is_file()]
    weights = [TARGET / MINILM / name for name in ("model.safetensors", "pytorch_model.bin")]
    if not any(path.is_file() for path in weights):
        problems.append(f"{MINILM}/model.safetensors (ya pytorch_model.bin)")
    return problems


def main():
    if not SOURCE.is_dir():
        print(f"ml/artifacts nahi mila: {SOURCE}")
        return 1
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir()

    try:
        copy_plain_folder("severity_experiments")
        copy_plain_folder("duplicates")
        copy_minilm()
        if copy_transformer():
            print("Transformer (version 2) bhi shamil kiya gaya.")
    except FileNotFoundError as error:
        print("Kaam nahi hua:", error)
        return 1

    problems = verify()
    if problems:
        print("Bundle adhoora hai, yeh files nahi milin:")
        for name in problems:
            print(f"  {name}")
        return 1

    for child in sorted(TARGET.iterdir()):
        size = folder_size_mb(child) if child.is_dir() else child.stat().st_size / (1024 * 1024)
        print(f"{size:8.1f} MB  {child.name}")
    print(f"{folder_size_mb(TARGET):8.1f} MB  kul ({TARGET})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
