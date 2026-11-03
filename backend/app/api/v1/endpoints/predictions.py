from fastapi import APIRouter, HTTPException, Request

from app.schemas.ml import (
    DuplicateRequest,
    DuplicateResponse,
    SeverityRequest,
    SeverityResponse,
)

router = APIRouter(tags=["predictions"])


def _get_model(request: Request, name: str, label: str):
    model = getattr(request.app.state, name, None)
    if model is None:
        raise HTTPException(status_code=503, detail=f"{label} model is not loaded")
    return model


@router.post("/severity/predict", response_model=SeverityResponse)
def predict_severity(body: SeverityRequest, request: Request):
    predictor = _get_model(request, "severity", "Severity")
    return predictor.predict([body.text], [body.project])[0]


@router.post("/duplicates/search", response_model=DuplicateResponse)
def search_duplicates(body: DuplicateRequest, request: Request):
    finder = _get_model(request, "finder", "Duplicate")
    threshold = finder.threshold if body.threshold is None else body.threshold
    hits = finder.find(body.text, top_k=body.top_k, threshold=threshold)
    return DuplicateResponse(candidates=hits, threshold=threshold)