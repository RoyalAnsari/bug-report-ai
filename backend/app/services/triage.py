from app.repositories.prediction_records import SEVERITY_MODEL_VERSION


def model_version_of(predictor, result=None):
    if result and result.get("model_version"):
        return result["model_version"]
    return getattr(predictor, "version", None) or SEVERITY_MODEL_VERSION


def run_triage(predictor, finder, text, project=None, top_k=5, min_similarity=0.5):
    """Ek report ka severity aur milte-julte purane reports. Kuch save nahi hota."""
    severity = predictor.predict([text], [project])[0]
    similar = []
    duplicate_threshold = None
    if finder is not None:
        duplicate_threshold = float(finder.threshold)
        for hit in finder.find(text, top_k=top_k, threshold=min_similarity):
            similar.append({**hit, "likely_duplicate": hit["similarity"] >= duplicate_threshold})
    return {
        "severity": severity,
        "similar": similar,
        "model_version": model_version_of(predictor, severity),
        "duplicate_threshold": duplicate_threshold,
    }
