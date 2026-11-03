from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request):
    state = request.app.state
    return {
        "status": "ok",
        "models": {
            "severity_loaded": state.severity is not None,
            "duplicates_loaded": state.finder is not None,
        },
    }