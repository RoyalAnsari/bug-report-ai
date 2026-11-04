"""model_bundle folder ko Hugging Face ke private repo par upload karta hai.

Pehle: python scripts/prepare_model_bundle.py
Phir (cmd mein, apna token set karke; token kisi ko na dikhayein):
    set HF_TOKEN=hf_xxx
    python scripts/upload_model_bundle.py YOUR-USERNAME/bug-report-ai-models
"""
import os
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / "model_bundle"


def main():
    if len(sys.argv) != 2:
        print("Istemal: python scripts/upload_model_bundle.py USERNAME/REPO-NAME")
        return 1
    repo_id = sys.argv[1]

    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        print("Pehle HF_TOKEN set karein (Hugging Face ka token, 'write' ijazat ke saath).")
        return 1
    if not BUNDLE.is_dir():
        print("model_bundle nahi mila. Pehle python scripts/prepare_model_bundle.py chalayein.")
        return 1

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="model", private=True, exist_ok=True)
    api.upload_folder(folder_path=str(BUNDLE), repo_id=repo_id, repo_type="model")
    print(f"Upload ho gaya (private repo): {repo_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
