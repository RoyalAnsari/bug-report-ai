from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.repositories import model_versions as versions_repo
from app.schemas.model_versions import ModelVersionOut, ModelVersionSummary

router = APIRouter(tags=["models"])


@router.get("/models", response_model=list[ModelVersionSummary])
async def list_models(db=Depends(get_db)):
    return await versions_repo.list_versions(db)


@router.get("/models/{name}/{version}", response_model=ModelVersionOut)
async def get_model(name: str, version: str, db=Depends(get_db)):
    model = await versions_repo.get_version(db, name, version)
    if model is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model