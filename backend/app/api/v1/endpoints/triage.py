from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.schemas.triage import TriageOut, TriageRequest
from app.services.triage import run_triage

router = APIRouter(tags=["triage"])


@router.post("/triage", response_model=TriageOut)
async def triage_report(body: TriageRequest, request: Request):
    """Naya bug likho: severity, confidence aur milte-julte purane bugs. Kuch save nahi hota."""
    predictor = getattr(request.app.state, "severity", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Severity model is not loaded")
    finder = getattr(request.app.state, "finder", None)
    return await run_in_threadpool(run_triage, predictor, finder, body.text, body.project, body.top_k)
