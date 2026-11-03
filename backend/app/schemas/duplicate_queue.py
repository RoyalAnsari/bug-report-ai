from pydantic import BaseModel

from app.schemas.duplicate_suggestions import SuggestionOut


class QueueItem(SuggestionOut):
    report_text: str | None = None
    report_project: str | None = None


class QueueList(BaseModel):
    items: list[QueueItem]
    total: int
    page: int
    page_size: int
    pages: int
