"""Severity ke liye fine-tune kiya hua transformer (DistilBERT). TF-IDF wale SeverityPredictor jaisa hi interface.

Yeh module import karte waqt torch ya transformers load nahi karta; woh model load karte waqt hi aate hain.
Model files ml/artifacts/severity_transformer mein hoti hain (ml/src/train_transformer.py ki output).
"""
import json
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
TRANSFORMER_DIR = REPO_ROOT / "ml" / "artifacts" / "severity_transformer"

# Sirf tab kaam aata hai jab calibrate_review_margin.py ki review_margin.json maujood na ho.
FALLBACK_REVIEW_MARGIN = 0.2
DEFAULT_MAX_LEN = 128


def build_input_text(text, project):
    """Bilkul wahi text jo train_transformer.py ne training mein diya tha."""
    text = " ".join(str(text).split())
    name = str(project or "unknown").strip().lower().replace(" ", "_")
    return f"{name}: {text}"


def version_from_model_name(model_name):
    return f"{str(model_name).split('/')[-1]}-v2"


def softmax(scores):
    shifted = scores - scores.max(axis=1, keepdims=True)
    exponent = np.exp(shifted)
    return exponent / exponent.sum(axis=1, keepdims=True)


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


class TransformerSeverityPredictor:
    """Severity predict karta hai. margin = sab se upar aur dusri class ki probability ka farq (0 se 1)."""

    def __init__(self, model, tokenizer, classes, offsets, review_margin=FALLBACK_REVIEW_MARGIN,
                 max_len=DEFAULT_MAX_LEN, batch_size=32, version="transformer-v2"):
        self.model = model
        self.tokenizer = tokenizer
        self.classes = list(classes)
        self.offsets = np.asarray(offsets, dtype=np.float64)
        if len(self.offsets) != len(self.classes):
            raise ValueError("offsets aur classes ki tadaad barabar honi chahiye")
        self.review_margin = float(review_margin)
        self.max_len = int(max_len)
        self.batch_size = int(batch_size)
        self.version = version

    @classmethod
    def from_artifact(cls, directory=TRANSFORMER_DIR, review_margin=None):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        directory = Path(directory)
        classes = json.loads((directory / "labels.json").read_text(encoding="utf-8"))
        offsets = json.loads((directory / "offsets.json").read_text(encoding="utf-8"))
        training = (_read_json(directory / "metrics.json") or {}).get("training", {})

        margin = review_margin
        if margin is None:
            saved = _read_json(directory / "review_margin.json")
            margin = saved["default"] if saved and "default" in saved else FALLBACK_REVIEW_MARGIN

        tokenizer = AutoTokenizer.from_pretrained(str(directory / "model"))
        model = AutoModelForSequenceClassification.from_pretrained(str(directory / "model"))
        model.eval()
        if model.config.num_labels != len(classes):
            raise ValueError("Model ki classes ki tadaad labels.json se mel nahi khati")
        return cls(
            model,
            tokenizer,
            classes,
            offsets,
            margin,
            max_len=int(training.get("max_len", DEFAULT_MAX_LEN)),
            version=version_from_model_name(training.get("model_name", "transformer")),
        )

    def _logits(self, inputs):
        import torch

        order = np.argsort([len(text) for text in inputs])
        logits = np.zeros((len(inputs), len(self.classes)), dtype=np.float64)
        with torch.inference_mode():
            for start in range(0, len(inputs), self.batch_size):
                indexes = order[start:start + self.batch_size]
                batch = self.tokenizer(
                    [inputs[i] for i in indexes],
                    truncation=True,
                    max_length=self.max_len,
                    padding=True,
                    return_tensors="pt",
                )
                feed = {key: batch[key] for key in ("input_ids", "attention_mask") if key in batch}
                logits[indexes] = self.model(**feed).logits.float().cpu().numpy()
        return logits

    def predict(self, texts, projects=None):
        texts = list(texts)
        if not texts:
            return []
        if projects is None:
            projects = [None] * len(texts)
        projects = list(projects)
        if len(projects) != len(texts):
            raise ValueError("texts aur projects ki tadaad barabar honi chahiye")

        inputs = [build_input_text(t, p) for t, p in zip(texts, projects)]
        scores = self._logits(inputs) + self.offsets
        probabilities = softmax(scores)

        results = []
        for row, probability in zip(scores, probabilities):
            order = np.argsort(-row)
            gap = float(probability[order[0]] - probability[order[1]])
            results.append(
                {
                    "label": self.classes[order[0]],
                    "margin": round(gap, 4),
                    "needs_review": gap < self.review_margin,
                    "scores": {c: round(float(s), 4) for c, s in zip(self.classes, row)},
                    "model_version": self.version,
                }
            )
        return results
