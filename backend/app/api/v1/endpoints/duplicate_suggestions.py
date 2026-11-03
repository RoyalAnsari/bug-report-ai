from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.repositories import duplicate_suggestions as suggestions_repo
from app.repositories import report_crud as reports_repo
from app.schemas.duplicate_suggestions import (
    FindDuplicatesRequest,
    FindDuplicatesResponse,
    SuggestionOut,
    SuggestionReviewRequest,
)

router = APIRouter(tags=["duplicate-suggestions"])


@router.post("/reports/{report_id}/duplicates/find", response_model=FindDuplicatesResponse)
async def find_duplicates(
    report_id: str,
    request: Request,
    body: FindDuplicatesRequest | None = None,
    db=Depends(get_db),
):
    finder = getattr(request.app.state, "finder", None)
    if finder is None:
        raise HTTPException(status_code=503, detail="Duplicate model is not loaded")

    report = await reports_repo.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    top_k = (body.top_k if body and body.top_k else None) or finder.top_k
    threshold = finder.threshold if body is None or body.threshold is None else body.threshold

    # Ek zyada maangte hain, taake report khud nikalne ke baad bhi top_k bache rahein
    hits = await run_in_threadpool(finder.find, report["text"], top_k + 1, threshold)
    hits = suggestions_repo.drop_self_matches(report, hits)[:top_k]

    outcome = await suggestions_repo.save_candidates(db, report_id, hits, threshold)
    suggestions = await suggestions_repo.list_suggestions(db, report_id)
    return FindDuplicatesResponse(
        report_id=report_id,
        threshold=threshold,
        found=len(hits),
        new=outcome["inserted"],
        suggestions=suggestions,
    )


@router.get("/reports/{report_id}/duplicates", response_model=list[SuggestionOut])
async def get_duplicates(
    report_id: str,
    db=Depends(get_db),
    status: Literal["pending", "confirmed", "rejected"] | None = Query(None),
):
    return await suggestions_repo.list_suggestions(db, report_id, status)


@router.post(
    "/duplicate-suggestions/{suggestion_id}/review",
    response_model=SuggestionOut,
    status_code=201,
)
async def review_duplicate(suggestion_id: str, body: SuggestionReviewRequest, db=Depends(get_db)):
    status, suggestion = await suggestions_repo.review_suggestion(
        db, suggestion_id, body.decision, body.note
    )
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if status == "exists":
        raise HTTPException(status_code=409, detail="This suggestion has already been reviewed")
    return suggestion