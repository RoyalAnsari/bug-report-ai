from fastapi import APIRouter

from app.api.v1.endpoints import (
    app_settings,
    bulk_predictions,
    dashboard,
    duplicate_queue,
    duplicate_suggestions,
    health,
    model_versions,
    predictions,
    report_facets,
    report_predictions,
    reports,
    reviews,
    uploads,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(predictions.router)
# report_facets must come before reports, so "/reports/projects" is not read as a report id
api_router.include_router(report_facets.router)
api_router.include_router(reports.router)
api_router.include_router(report_predictions.router)
api_router.include_router(bulk_predictions.router)
api_router.include_router(uploads.router)
api_router.include_router(dashboard.router)
api_router.include_router(reviews.router)
api_router.include_router(duplicate_suggestions.router)
api_router.include_router(duplicate_queue.router)
api_router.include_router(model_versions.router)
api_router.include_router(app_settings.router)
