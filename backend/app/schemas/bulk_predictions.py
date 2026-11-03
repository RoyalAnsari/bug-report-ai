from pydantic import BaseModel, Field


class BulkRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=500)


class BulkStatus(BaseModel):
    total_reports: int
    reports_with_predictions: int
    unpredicted: int


class BulkResult(BaseModel):
    requested: int
    predicted: int
    needs_review: int
    remaining: int
    model_version: str
    note: str = "margin is a score gap, not a probability"
