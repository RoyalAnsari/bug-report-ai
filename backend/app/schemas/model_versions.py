from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ModelVersionSummary(BaseModel):
    id: str
    name: str
    version: str
    task: str
    has_evaluation: bool
    macro_f1: float | None = None
    created_at: datetime | None = None


class ModelVersionOut(BaseModel):
    id: str
    name: str
    version: str
    task: str
    algorithm: str
    variant: str | None = None
    uses_offsets: bool | None = None
    labels: list[str] | None = None
    artifact_path: str | None = None
    training: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    evaluation_note: str | None = None
    config: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None