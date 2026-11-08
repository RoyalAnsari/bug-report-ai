from app.ml.transformer_inference import version_from_model_name
from app.repositories.model_versions import SEVERITY_NAME, extract_evaluation


def build_transformer_document(metrics):
    """Transformer ki metrics.json (train_transformer.py ki output) se model_versions ka document banata hai."""
    chosen = metrics["chosen"]
    test = metrics["test"]
    training = metrics.get("training", {})
    model_name = training.get("model_name", "transformer")
    version = version_from_model_name(model_name)
    return {
        "_id": f"{SEVERITY_NAME}:{version}",
        "name": SEVERITY_NAME,
        "version": version,
        "task": "severity classification",
        "algorithm": f"Fine-tuned transformer ({model_name})",
        "variant": chosen["variant"],
        "uses_offsets": bool(chosen["offsets"]),
        "labels": test["labels_order"],
        "artifact_path": "ml/artifacts/severity_transformer",
        "training": {
            "seed": training.get("seed"),
            "resample_target": None,
            "validation_macro_f1": chosen.get("val_macro_f1"),
            "library_versions": metrics.get("versions"),
        },
        "evaluation": {"split": "test", **extract_evaluation(test)},
        "evaluation_note": None,
        "config": None,
    }
