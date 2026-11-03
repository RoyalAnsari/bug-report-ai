from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.repositories import report_facets as facets_repo
from app.schemas.report_facets import ProjectList

router = APIRouter(tags=["reports"])


@router.get("/reports/projects", response_model=ProjectList)
async def get_projects(db=Depends(get_db)):
    return ProjectList(projects=await facets_repo.list_projects(db))
