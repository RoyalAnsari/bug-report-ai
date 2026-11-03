from pydantic import BaseModel, ConfigDict, Field


class SeverityRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=3, max_length=2000)
    project: str | None = Field(default=None, max_length=100)


class SeverityResponse(BaseModel):
    label: str
    margin: float
    needs_review: bool
    scores: dict[str, float]
    note: str = "margin is a score gap, not a probability"


class DuplicateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class DuplicateCandidate(BaseModel):
    bug_id: int
    project: str
    text: str
    similarity: float


class DuplicateResponse(BaseModel):
    candidates: list[DuplicateCandidate]
    threshold: float
    score_type: str = "cosine similarity (not a probability)"