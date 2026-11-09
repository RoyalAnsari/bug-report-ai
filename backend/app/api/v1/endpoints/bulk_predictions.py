from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.repositories import bulk_predictions as bulk_repo
from app.repositories.prediction_records import SEVERITY_MODEL_VERSION, build_prediction_document
from app.schemas.bulk_predictions import BulkRequest, BulkResult, BulkStatus
from app.services.bulk_predict import BATCH_SIZE, predict_in_batches

router = APIRouter(tags=["bulk-predictions"])


@router.get("/predictions/bulk/status", response_model=BulkStatus)
async def bulk_status(db=Depends(get_db)):
    return await bulk_repo.count_unpredicted(db)


@router.post("/predictions/bulk", response_model=BulkResult)
async def bulk_predict(body: BulkRequest, request: Request, db=Depends(get_db)):
    predictor = getattr(request.app.state, "severity", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Severity model is not loaded")
    version = getattr(predictor, "version", SEVERITY_MODEL_VERSION)

    reports = await bulk_repo.find_unpredicted(db, body.limit)
    if not reports:
        counts = await bulk_repo.count_unpredicted(db)
        return BulkResult(
            requested=0,
            predicted=0,
            needs_review=0,
            remaining=counts["unpredicted"],
            model_version=version,
        )

    pairs = await run_in_threadpool(predict_in_batches, predictor, reports, BATCH_SIZE)
    documents = [build_prediction_document(report_id, result) for report_id, result in pairs]
    await bulk_repo.save_many(db, documents)

    counts = await bulk_repo.count_unpredicted(db)
    return BulkResult(
        requested=len(reports),
        predicted=len(documents),
        needs_review=sum(1 for document in documents if document["needs_review"]),
        remaining=counts["unpredicted"],
        model_version=version,
    )
