import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

# Abhi cosine search ka code ml\src\duplicates.py se liya ja raha hai (copy se bachne ke liye).
sys.path.insert(0, str(REPO_ROOT / "ml" / "src"))
from duplicates import top_k_similar  # noqa: E402

SEVERITY_MODEL_PATH = REPO_ROOT / "ml" / "artifacts" / "severity_experiments" / "model.joblib"
DUPLICATES_DIR = REPO_ROOT / "ml" / "artifacts" / "duplicates"
MINILM_DIR = REPO_ROOT / "ml" / "artifacts" / "models" / "all-MiniLM-L6-v2"

DEFAULT_REVIEW_MARGIN = 0.25  # shuruaati andaaza, tested nahi
DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.80  # shuruaati andaaza, tested nahi


def build_input_text(text, project, use_project):
    """Bilkul wahi text banata hai jo training mein use hua tha."""
    text = " ".join(str(text).split())
    if not use_project:
        return text
    name = str(project or "unknown").strip().lower().replace(" ", "_")
    return f"proj{name} {text}"


class SeverityPredictor:
    """Severity predict karta hai aur margin dikhata hai (probability nahi)."""

    def __init__(self, model, classes, offsets, use_project, review_margin=DEFAULT_REVIEW_MARGIN):
        self.model = model
        self.classes = list(classes)
        self.offsets = np.asarray(offsets, dtype=np.float64)
        self.use_project = bool(use_project)
        self.review_margin = float(review_margin)

    @classmethod
    def from_artifact(cls, path=SEVERITY_MODEL_PATH, review_margin=DEFAULT_REVIEW_MARGIN):
        artifact = joblib.load(path)
        return cls(
            artifact["model"],
            artifact["classes"],
            artifact["offsets"],
            artifact["use_project"],
            review_margin,
        )

    def predict(self, texts, projects=None):
        texts = list(texts)
        if not texts:
            return []
        if projects is None:
            projects = [None] * len(texts)
        projects = list(projects)
        if len(projects) != len(texts):
            raise ValueError("texts aur projects ki tadaad barabar honi chahiye")

        inputs = [build_input_text(t, p, self.use_project) for t, p in zip(texts, projects)]
        scores = self.model.decision_function(inputs) + self.offsets

        results = []
        for row in scores:
            order = np.argsort(-row)
            margin = float(row[order[0]] - row[order[1]])
            results.append(
                {
                    "label": self.classes[order[0]],
                    "margin": round(margin, 4),
                    "needs_review": margin < self.review_margin,
                    "scores": {c: round(float(s), 4) for c, s in zip(self.classes, row)},
                }
            )
        return results


class DuplicateFinder:
    """Naye report ke milte julte purane reports dhoondta hai (cosine similarity)."""

    def __init__(self, encoder, embeddings, reports, top_k=DEFAULT_TOP_K,
                 threshold=DEFAULT_THRESHOLD, batch_size=64):
        embeddings = np.asarray(embeddings, dtype=np.float32)
        if len(reports) != len(embeddings):
            raise ValueError(
                f"reports ({len(reports)}) aur embeddings ({len(embeddings)}) ki tadaad alag hai"
            )
        self.encoder = encoder
        self.embeddings = embeddings
        self.reports = reports.reset_index(drop=True)
        self.top_k = top_k
        self.threshold = threshold
        self.batch_size = batch_size

    @classmethod
    def from_artifacts(cls, directory=DUPLICATES_DIR, model_dir=MINILM_DIR):
        from sentence_transformers import SentenceTransformer

        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        embeddings = np.load(directory / "embeddings.npy")
        reports = pd.read_csv(directory / "reports_index.csv", encoding="utf-8")
        encoder = SentenceTransformer(str(model_dir), device="cpu")
        return cls(
            encoder,
            embeddings,
            reports,
            top_k=config.get("default_top_k", DEFAULT_TOP_K),
            threshold=config.get("default_threshold", DEFAULT_THRESHOLD),
            batch_size=config.get("batch_size", 64),
        )

    def find(self, text, top_k=None, threshold=None):
        top_k = self.top_k if top_k is None else top_k
        threshold = self.threshold if threshold is None else threshold
        if top_k < 1:
            raise ValueError("top_k kam se kam 1 hona chahiye")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold 0 aur 1 ke beech hona chahiye")

        vector = self.encoder.encode(
            [str(text)],
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        hits = top_k_similar(vector, self.embeddings, k=top_k, threshold=threshold)[0]
        return [
            {
                "bug_id": int(self.reports.iloc[i]["bug_id"]),
                "project": str(self.reports.iloc[i]["project"]),
                "text": str(self.reports.iloc[i]["text"]),
                "similarity": round(score, 4),
            }
            for i, score in hits
        ]