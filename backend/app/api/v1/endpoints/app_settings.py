from fastapi import APIRouter, Depends, Request

from app.api.deps import get_db
from app.repositories import app_settings as settings_repo
from app.schemas.app_settings import ApplicationInfo, ModelsLoaded, SettingsResponse, SettingsValues
from app.services.app_settings import apply_to_state, merge_with_defaults

router = APIRouter(tags=["settings"])


def build_response(request: Request, values, updated_at):
    state = request.app.state
    config = state.config
    return SettingsResponse(
        values=SettingsValues(**values),
        defaults=SettingsValues(**state.defaults),
        application=ApplicationInfo(
            api_version="v1",
            cors_origins=list(config.cors_origins),
            database=config.mongodb_db,
            models_loaded=ModelsLoaded(
                severity=state.severity is not None,
                duplicates=state.finder is not None,
            ),
        ),
        updated_at=updated_at,
    )


@router.get("/settings", response_model=SettingsResponse)
async def read_settings(request: Request, db=Depends(get_db)):
    saved = await settings_repo.get_saved(db)
    values = merge_with_defaults(request.app.state.defaults, saved)
    return build_response(request, values, saved.get("updated_at"))


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(body: SettingsValues, request: Request, db=Depends(get_db)):
    values = body.model_dump()
    updated_at = await settings_repo.save(db, values)
    apply_to_state(request.app.state, values)
    return build_response(request, values, updated_at)


@router.post("/settings/reset", response_model=SettingsResponse)
async def reset_settings(request: Request, db=Depends(get_db)):
    await settings_repo.clear(db)
    defaults = dict(request.app.state.defaults)
    apply_to_state(request.app.state, defaults)
    return build_response(request, defaults, None)
