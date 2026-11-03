from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.repositories import prediction_records as predictions_repo
from app.repositories import report_crud as reports_repo
from app.schemas.prediction_records import PredictionOut

router = APIRouter(tags=["report-predictions"])


@router.post("/reports/{report_id}/predict", response_model=PredictionOut, status_code=201)
async def predict_report(report_id: str, request: Request, db=Depends(get_db)):
    predictor = getattr(request.app.state, "severity", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Severity model is not loaded")

    report = await reports_repo.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    results = await run_in_threadpool(predictor.predict, [report["text"]], [report["project"]])
    return await predictions_repo.save_prediction(db, report_id, results[0])


@router.get("/reports/{report_id}/predictions", response_model=list[PredictionOut])
async def get_report_predictions(
    report_id: str,
    db=Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    if await reports_repo.get_report(db, report_id) is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return await predictions_repo.list_predictions(db, report_id, limit=limit)