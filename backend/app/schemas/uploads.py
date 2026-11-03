from pydantic import BaseModel


class RowError(BaseModel):
    row: int
    message: str


class UploadPreview(BaseModel):
    filename: str
    encoding: str
    headers: list[str]
    mapping: dict[str, str | None]
    needs_mapping: bool
    preview: list[dict[str, str]]
    total_rows: int
    valid_rows: int
    error_count: int
    errors: list[RowError]
    errors_truncated: bool


class ImportResult(BaseModel):
    total_rows: int
    valid_rows: int
    error_count: int
    errors: list[RowError]
    errors_truncated: bool
    inserted: int
    already_existed: int
    merged_duplicates: int