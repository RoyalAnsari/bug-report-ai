from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_reports: int
    severity_distribution: dict[str, int]
    predictions_total: int
    reports_with_predictions: int
    pending_reviews: int
    duplicate_suggestions: dict[str, int]
    duplicate_suggestions_total: int