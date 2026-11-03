import os
from dataclasses import dataclass, field


def _split(value):
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Bug Report Classifier API"
    cors_origins: tuple = ("http://localhost:5173",)
    review_margin: float = 0.25
    load_models: bool = True
    mongodb_uri: str = field(default="", repr=False)
    mongodb_db: str = "bug_report_ai"

    @classmethod
    def from_env(cls):
        """Settings environment variables se leta hai (koi secret code mein nahi)."""
        return cls(
            cors_origins=tuple(_split(os.getenv("CORS_ORIGINS", "http://localhost:5173"))),
            review_margin=float(os.getenv("REVIEW_MARGIN", "0.25")),
            load_models=os.getenv("LOAD_MODELS", "true").lower() != "false",
            mongodb_uri=os.getenv("MONGODB_URI", ""),
            mongodb_db=os.getenv("MONGODB_DB", "bug_report_ai"),
        )