from pydantic import BaseModel, Field, field_validator


class TriageRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    project: str | None = Field(default=None, max_length=100)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value):
        value = " ".join(value.split())
        if len(value) < 3:
            raise ValueError("The text is too short")
        return value


class SeverityOut(BaseModel):
    label: str
    margin: float
    needs_review: bool
    scores: dict[str, float]


class SimilarOut(BaseModel):
    bug_id: int
    project: str
    text: str
    similarity: float
    likely_duplicate: bool


class TriageOut(BaseModel):
    severity: SeverityOut
    similar: list[SimilarOut]
    model_version: str
    duplicate_threshold: float | None = None


class ClassMetric(BaseModel):
    label: str
    precision: float
    recall: float
    f1: float
    support: int


class EvaluationOut(BaseModel):
    model_version: str
    rows_used: int
    rows_skipped: int
    skipped_examples: list[str]
    accuracy: float
    macro_f1: float
    majority_baseline_accuracy: float
    labels: list[str]
    per_class: list[ClassMetric]
    confusion_matrix: list[list[int]]
    warnings: list[str]
