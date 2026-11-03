import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_db
from app.repositories import bug_reports as reports_repo
from app.schemas.uploads import ImportResult, UploadPreview
from app.services.csv_validation import (
    FIELD_CANDIDATES,
    MAX_FILE_BYTES,
    CsvValidationError,
    read_csv_rows,
    suggest_mapping,
    validate_rows,
)

router = APIRouter(tags=["uploads"])

ALLOWED_FIELDS = tuple(FIELD_CANDIDATES)


def parse_mapping(raw):
    """Form se aaya mapping (JSON text) check karta hai. Khali ho to None."""
    if raw is None or not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="mapping must be valid JSON")
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail="mapping must be a JSON object")
    unknown = set(value) - set(ALLOWED_FIELDS)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mapping fields: {sorted(unknown)}. Allowed: {list(ALLOWED_FIELDS)}",
        )
    cleaned = {}
    for field_name in ALLOWED_FIELDS:
        column = value.get(field_name)
        if column is not None and not isinstance(column, str):
            raise HTTPException(status_code=400, detail=f"mapping for '{field_name}' must be text")
        cleaned[field_name] = column or None
    return cleaned


def analyze_upload(data, filename, raw_mapping):
    """File ki poori jaanch. Preview aur import dono isi ko use karte hain."""
    mapping = parse_mapping(raw_mapping)
    try:
        headers, rows, encoding = read_csv_rows(data, filename)
        if mapping is None:
            mapping = suggest_mapping(headers)
        base = {
            "filename": filename[:200],
            "encoding": encoding,
            "headers": headers,
            "mapping": mapping,
            "preview": rows[:5],
            "total_rows": len(rows),
        }
        if not mapping.get("text"):
            return {
                **base,
                "needs_mapping": True,
                "valid_rows": 0,
                "error_count": 0,
                "errors": [],
                "errors_truncated": False,
                "valid": [],
            }
        result = validate_rows(headers, rows, mapping)
    except CsvValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        **base,
        "needs_mapping": False,
        "valid_rows": result["valid_rows"],
        "error_count": result["error_count"],
        "errors": result["errors"],
        "errors_truncated": result["errors_truncated"],
        "valid": result["valid"],
    }


@router.post("/uploads/preview", response_model=UploadPreview)
async def preview_upload(file: UploadFile = File(...), mapping: str | None = Form(None)):
    data = await file.read(MAX_FILE_BYTES + 1)
    return analyze_upload(data, file.filename or "", mapping)


@router.post("/uploads/import", response_model=ImportResult)
async def import_upload(
    file: UploadFile = File(...),
    mapping: str | None = Form(None),
    db=Depends(get_db),
):
    data = await file.read(MAX_FILE_BYTES + 1)
    filename = file.filename or "upload.csv"
    analysis = analyze_upload(data, filename, mapping)
    if analysis["needs_mapping"]:
        raise HTTPException(status_code=400, detail="Choose which column holds the bug text")
    if analysis["valid_rows"] == 0:
        raise HTTPException(status_code=400, detail="No valid rows to import")

    outcome = await reports_repo.upsert_reports(
        db, analysis["valid"], source=f"csv:{filename[:100]}"
    )
    merged = analysis["valid_rows"] - outcome["inserted"] - outcome["already_existed"]
    return {
        "total_rows": analysis["total_rows"],
        "valid_rows": analysis["valid_rows"],
        "error_count": analysis["error_count"],
        "errors": analysis["errors"],
        "errors_truncated": analysis["errors_truncated"],
        "inserted": outcome["inserted"],
        "already_existed": outcome["already_existed"],
        "merged_duplicates": merged,
    }