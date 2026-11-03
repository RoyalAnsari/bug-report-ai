from datetime import datetime

from pydantic import BaseModel, Field


class SettingsValues(BaseModel):
    review_margin: float = Field(ge=0.0, le=5.0)
    duplicate_threshold: float = Field(ge=0.0, le=1.0)
    duplicate_top_k: int = Field(ge=1, le=50)


class ModelsLoaded(BaseModel):
    severity: bool
    duplicates: bool


class ApplicationInfo(BaseModel):
    api_version: str
    cors_origins: list[str]
    database: str
    models_loaded: ModelsLoaded


class SettingsResponse(BaseModel):
    values: SettingsValues
    defaults: SettingsValues
    application: ApplicationInfo
    updated_at: datetime | None = None
