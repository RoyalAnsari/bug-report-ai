import os
from dataclasses import dataclass, field


def _split(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _flag(name, default):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Bug Report Classifier API"
    cors_origins: tuple = ("http://localhost:5173",)
    review_margin: float = 0.25
    load_models: bool = True
    mongodb_uri: str = field(default="", repr=False)
    mongodb_db: str = "bug_report_ai"
    # Login. Code ka default False hai (tests ke liye), lekin from_env() mein default True hai.
    auth_enabled: bool = False
    jwt_secret: str = field(default="", repr=False)
    access_token_minutes: int = 60
    # Ghalat password ki koshishon par account kuch der ke liye band.
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    # /docs, /redoc aur /openapi.json. Production mein band rakhein.
    enable_docs: bool = False
    # HTTPS par deploy karte waqt True karein.
    enable_hsts: bool = False

    @classmethod
    def from_env(cls):
        """Settings environment variables se leta hai (koi secret code mein nahi)."""
        return cls(
            cors_origins=tuple(_split(os.getenv("CORS_ORIGINS", "http://localhost:5173"))),
            review_margin=float(os.getenv("REVIEW_MARGIN", "0.25")),
            load_models=os.getenv("LOAD_MODELS", "true").lower() != "false",
            mongodb_uri=os.getenv("MONGODB_URI", ""),
            mongodb_db=os.getenv("MONGODB_DB", "bug_report_ai"),
            auth_enabled=os.getenv("AUTH_ENABLED", "true").lower() != "false",
            jwt_secret=os.getenv("JWT_SECRET", ""),
            access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "60")),
            max_failed_logins=int(os.getenv("MAX_FAILED_LOGINS", "5")),
            lockout_minutes=int(os.getenv("LOCKOUT_MINUTES", "15")),
            enable_docs=_flag("ENABLE_DOCS", "false"),
            enable_hsts=_flag("ENABLE_HSTS", "false"),
        )

    def validate_for_startup(self):
        """Server shuru hone se pehle ghalat ya kamzor settings pakadta hai."""
        if self.auth_enabled and len(self.jwt_secret) < 32:
            raise ValueError(
                "JWT_SECRET must be set and at least 32 characters long when AUTH_ENABLED is true. "
                "Create one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if self.access_token_minutes < 1:
            raise ValueError("ACCESS_TOKEN_MINUTES must be at least 1")
        if self.max_failed_logins < 1 or self.lockout_minutes < 1:
            raise ValueError("MAX_FAILED_LOGINS and LOCKOUT_MINUTES must be at least 1")
