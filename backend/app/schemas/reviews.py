from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.reports import Severity


class ReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: Literal["confirm", "correct"]
    label: Severity | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_label(self):
        if self.action == "correct" and self.label is None:
            raise ValueError("label is required when action is 'correct'")
        if self.action == "confirm" and self.label is not None:
            raise ValueError("label must not be given when action is 'confirm'")
        return self


class ReviewOut(BaseModel):
    id: str
    prediction_id: str
    report_id: str
    action: str
    predicted_label: str
    final_label: str
    note: str | None = None
    created_at: datetime | None = None