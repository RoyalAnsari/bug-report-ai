from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.repositories import reviews as reviews_repo
from app.schemas.reviews import ReviewOut, ReviewRequest

router = APIRouter(tags=["reviews"])


@router.post("/predictions/{prediction_id}/review", response_model=ReviewOut, status_code=201)
async def review_prediction(prediction_id: str, body: ReviewRequest, db=Depends(get_db)):
    status, review = await reviews_repo.submit_review(
        db, prediction_id, body.action, body.label, body.note
    )
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Prediction not found")
    if status == "exists":
        raise HTTPException(status_code=409, detail="This prediction has already been reviewed")
    return review


@router.get("/predictions/{prediction_id}/review", response_model=ReviewOut)
async def get_prediction_review(prediction_id: str, db=Depends(get_db)):
    review = await reviews_repo.get_review(db, prediction_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review