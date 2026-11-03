FALLBACK_THRESHOLD = 0.8
FALLBACK_TOP_K = 5
KEYS = ("review_margin", "duplicate_threshold", "duplicate_top_k")


def build_defaults(config, finder=None):
    """The values the app starts with when nothing was saved."""
    return {
        "review_margin": float(config.review_margin),
        "duplicate_threshold": float(finder.threshold) if finder is not None else FALLBACK_THRESHOLD,
        "duplicate_top_k": int(finder.top_k) if finder is not None else FALLBACK_TOP_K,
    }


def merge_with_defaults(defaults, saved):
    """Saved values win. Missing values and unknown keys are ignored."""
    values = {}
    for key in KEYS:
        value = saved.get(key)
        values[key] = defaults[key] if value is None else value
    return {
        "review_margin": float(values["review_margin"]),
        "duplicate_threshold": float(values["duplicate_threshold"]),
        "duplicate_top_k": int(values["duplicate_top_k"]),
    }


def apply_to_state(state, values):
    """Gives the values to the models that are loaded. Models that are not loaded are skipped."""
    severity = getattr(state, "severity", None)
    if severity is not None:
        severity.review_margin = float(values["review_margin"])
    finder = getattr(state, "finder", None)
    if finder is not None:
        finder.threshold = float(values["duplicate_threshold"])
        finder.top_k = int(values["duplicate_top_k"])
