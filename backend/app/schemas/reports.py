from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["blocker", "critical", "major", "normal", "minor", "trivial"]


class ReportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=3, max_length=2000)
    project: str | None = Field(default=None, max_length=100)
    severity: Severity | None = None


class ReportUpdate(BaseModel):
    severity: Severity


class ReportOut(BaseModel):
    id: str
    text: str
    project: str | None = None
    severity: str | None = None
    external_id: str | None = None
    source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReportList(BaseModel):
    items: list[ReportOut]
    total: int
    page: int
    page_size: int
    pages: int