from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.api.deps import get_db, require_admin
from app.repositories import report_crud as repo
from app.schemas.reports import ReportCreate, ReportList, ReportOut, ReportUpdate, Severity

router = APIRouter(tags=["reports"])

SortField = Literal["created_at", "updated_at", "project", "severity"]


@router.get("/reports", response_model=ReportList)
async def get_reports(
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    project: str | None = Query(None, max_length=100),
    severity: Severity | None = None,
    sort_by: SortField = "created_at",
    order: Literal["asc", "desc"] = "desc",
):
    result = await repo.list_reports(
        db,
        page=page,
        page_size=page_size,
        search=search,
        project=project,
        severity=severity,
        sort_by=sort_by,
        order=order,
    )
    return ReportList(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=repo.page_count(result["total"], page_size),
    )


@router.post("/reports", response_model=ReportOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_report(body: ReportCreate, db=Depends(get_db)):
    report = await repo.create_report(db, body.model_dump())
    if report is None:
        raise HTTPException(status_code=409, detail="This report already exists")
    return report


@router.get("/reports/{report_id}", response_model=ReportOut)
async def get_report(report_id: str, db=Depends(get_db)):
    report = await repo.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/reports/{report_id}", response_model=ReportOut)
async def update_report(report_id: str, body: ReportUpdate, db=Depends(get_db)):
    report = await repo.update_severity(db, report_id, body.severity)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/reports/{report_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_report(report_id: str, db=Depends(get_db)):
    if not await repo.delete_report(db, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=204)
