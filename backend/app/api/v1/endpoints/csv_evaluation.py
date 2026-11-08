from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.schemas.triage import EvaluationOut
from app.services.csv_evaluation import (
    MAX_BYTES,
    CsvProblem,
    build_warnings,
    compute_metrics,
    parse_labeled_csv,
    predict_all,
)
from app.services.triage import model_version_of

router = APIRouter(tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationOut)
async def evaluate_labeled_csv(request: Request, file: UploadFile = File(...)):
    """Labelled CSV par model ka accuracy aur F1. Kuch save nahi hota."""
    predictor = getattr(request.app.state, "severity", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Severity model is not loaded")

    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="The file is too large (the limit is 2 MB)")
    try:
        rows, skipped, examples = parse_labeled_csv(data)
    except CsvProblem as problem:
        raise HTTPException(status_code=400, detail=str(problem))
    if not rows:
        raise HTTPException(status_code=400, detail="No usable rows in the file")

    predicted = await run_in_threadpool(predict_all, predictor, rows)
    metrics = compute_metrics([row[2] for row in rows], predicted)
    return {
        "model_version": model_version_of(predictor),
        "rows_used": len(rows),
        "rows_skipped": skipped,
        "skipped_examples": examples,
        "warnings": build_warnings(len(rows), metrics["per_class"]),
        **metrics,
    }
