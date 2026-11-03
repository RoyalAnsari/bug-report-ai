from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FindDuplicatesRequest(BaseModel):
    top_k: int | None = Field(default=None, ge=1, le=50)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class SuggestionOut(BaseModel):
    id: str
    report_id: str
    candidate_id: str
    candidate_text: str
    candidate_project: str | None = None
    similarity: float
    score_type: str
    status: str
    created_at: datetime | None = None


class FindDuplicatesResponse(BaseModel):
    report_id: str
    threshold: float
    found: int
    new: int
    suggestions: list[SuggestionOut]


class SuggestionReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    decision: Literal["confirm", "reject"]
    note: str | None = Field(default=None, max_length=500)