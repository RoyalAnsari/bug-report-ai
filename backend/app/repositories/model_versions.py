from datetime import datetime, timezone

from app.db.collections import MODEL_VERSIONS
from app.repositories.prediction_records import SEVERITY_MODEL_VERSION

SEVERITY_NAME = "severity-classifier"
DUPLICATE_NAME = "duplicate-detector"
DUPLICATE_MODEL_VERSION = "minilm-l6-v2-index-v1"  # haath se rakha naam
DUPLICATE_NOTE = (
    "No verified duplicate pairs are available, so precision and recall were not measured."
)
DUPLICATE_CONFIG_KEYS = (
    "model", "rows", "embedding_dim", "normalized", "score_type",
    "batch_size", "default_top_k", "default_threshold", "created_utc",
)


def extract_evaluation(split_metrics):
    """Training ki metrics se sirf labels ki rows aur macro numbers nikalta hai."""
    labels = split_metrics["labels_order"]
    per_class = {}
    for label in labels:
        row = split_metrics["per_class"][label]
        per_class[label] = {
            "precision": row["precision"],
            "recall": row["recall"],
            "f1": row["f1-score"],
            "support": int(row["support"]),
        }
    macro = split_metrics["per_class"].get("macro avg", {})
    return {
        "macro_f1": split_metrics["macro_f1"],
        "macro_precision": macro.get("precision"),
        "macro_recall": macro.get("recall"),
        "per_class": per_class,
        "confusion_matrix": split_metrics["confusion_matrix"],
        "labels_order": labels,
        "rows": split_metrics["rows"],
    }


def build_severity_document(metrics, version=SEVERITY_MODEL_VERSION):
    chosen = metrics["chosen"]
    test = metrics["test"]
    return {
        "_id": f"{SEVERITY_NAME}:{version}",
        "name": SEVERITY_NAME,
        "version": version,
        "task": "severity classification",
        "algorithm": "TF-IDF + LinearSVC",
        "variant": chosen["variant"],
        "uses_offsets": bool(chosen["offsets"]),
        "labels": test["labels_order"],
        "artifact_path": "ml/artifacts/severity_experiments/model.joblib",
        "training": {
            "seed": metrics.get("seed"),
            "resample_target": metrics.get("resample_target"),
            "validation_macro_f1": chosen.get("val_macro_f1"),
            "library_versions": metrics.get("versions"),
        },
        "evaluation": {"split": "test", **extract_evaluation(test)},
        "evaluation_note": None,
        "config": None,
    }


def build_duplicate_document(config, version=DUPLICATE_MODEL_VERSION):
    return {
        "_id": f"{DUPLICATE_NAME}:{version}",
        "name": DUPLICATE_NAME,
        "version": version,
        "task": "duplicate candidate retrieval",
        "algorithm": "Sentence Transformer embeddings + cosine similarity",
        "variant": config.get("model"),
        "uses_offsets": None,
        "labels": None,
        "artifact_path": "ml/artifacts/duplicates",
        "training": None,
        "evaluation": None,
        "evaluation_note": DUPLICATE_NOTE,
        "config": {key: config.get(key) for key in DUPLICATE_CONFIG_KEYS},
    }


def to_summary(doc):
    evaluation = doc.get("evaluation")
    return {
        "id": doc["_id"],
        "name": doc["name"],
        "version": doc["version"],
        "task": doc["task"],
        "has_evaluation": bool(evaluation),
        "macro_f1": evaluation["macro_f1"] if evaluation else None,
        "created_at": doc.get("created_at"),
    }


def to_out(doc):
    return {
        "id": doc["_id"],
        "name": doc["name"],
        "version": doc["version"],
        "task": doc["task"],
        "algorithm": doc["algorithm"],
        "variant": doc.get("variant"),
        "uses_offsets": doc.get("uses_offsets"),
        "labels": doc.get("labels"),
        "artifact_path": doc.get("artifact_path"),
        "training": doc.get("training"),
        "evaluation": doc.get("evaluation"),
        "evaluation_note": doc.get("evaluation_note"),
        "config": doc.get("config"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def upsert_version(db, document):
    """Version dalta hai. Dobara chalane par purani created_at wahi rehti hai."""
    now = datetime.now(timezone.utc)
    fields = {k: v for k, v in document.items() if k not in ("_id", "created_at")}
    fields["updated_at"] = now
    await db[MODEL_VERSIONS].update_one(
        {"_id": document["_id"]},
        {"$set": fields, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )


async def list_versions(db):
    cursor = db[MODEL_VERSIONS].find({}).sort([("created_at", -1), ("_id", 1)])
    return [to_summary(doc) async for doc in cursor]


async def get_version(db, name, version):
    doc = await db[MODEL_VERSIONS].find_one({"name": name, "version": version})
    return to_out(doc) if doc else None