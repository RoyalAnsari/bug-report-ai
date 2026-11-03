from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]

DATASET_ID = "AliArshad/Bugzilla_Eclipse_Bug_Reports_Dataset"
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

dataset_dir = ROOT / "data" / "raw" / "bugzilla_eclipse"
model_dir = ROOT / "artifacts" / "models" / "all-MiniLM-L6-v2"

print("Downloading dataset...")
snapshot_download(repo_id=DATASET_ID, repo_type="dataset", local_dir=dataset_dir)

print("Downloading model...")
snapshot_download(repo_id=MODEL_ID, local_dir=model_dir)

print("Done.")
print("Dataset folder:", dataset_dir)
print("Model folder:", model_dir)