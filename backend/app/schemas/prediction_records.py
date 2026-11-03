from datetime import datetime

from pydantic import BaseModel


class PredictionOut(BaseModel):
    id: str
    report_id: str
    label: str
    margin: float
    needs_review: bool
    scores: dict[str, float]
    model_version: str
    created_at: datetime | None = None
    note: str = "margin is a score gap, not a probability"