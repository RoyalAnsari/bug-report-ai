from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.repositories import dashboard as dashboard_repo
from app.schemas.dashboard import DashboardSummary

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(db=Depends(get_db)):
    return await dashboard_repo.get_summary(db)