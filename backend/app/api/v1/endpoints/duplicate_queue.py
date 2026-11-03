from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.repositories import duplicate_queue as queue_repo
from app.repositories.report_crud import page_count
from app.schemas.duplicate_queue import QueueList

router = APIRouter(tags=["duplicate-suggestions"])


@router.get("/duplicate-suggestions", response_model=QueueList)
async def get_duplicate_queue(
    db=Depends(get_db),
    status: Literal["pending", "confirmed", "rejected", "all"] = "pending",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    result = await queue_repo.list_queue(
        db,
        status=None if status == "all" else status,
        page=page,
        page_size=page_size,
    )
    return QueueList(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=page_count(result["total"], page_size),
    )
