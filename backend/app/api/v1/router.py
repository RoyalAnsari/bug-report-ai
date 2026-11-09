from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_admin
from app.api.v1.endpoints import (
    app_settings,
    auth,
    bulk_predictions,
    csv_evaluation,
    dashboard,
    duplicate_queue,
    duplicate_suggestions,
    github_webhook,
    health,
    model_versions,
    predictions,
    report_facets,
    report_predictions,
    reports,
    reviews,
    triage,
    uploads,
    users,
)

api_router = APIRouter()

signed_in = [Depends(get_current_user)]  # admin ya reviewer
admin_only = [Depends(require_admin)]

# Bina login: health check aur login.
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(github_webhook.router)

# Order pehle jaisa hi hai (route ke takraav se bachne ke liye).
api_router.include_router(predictions.router, dependencies=signed_in)
# report_facets must come before reports, so "/reports/projects" is not read as a report id
api_router.include_router(report_facets.router, dependencies=signed_in)
api_router.include_router(reports.router, dependencies=signed_in)
api_router.include_router(report_predictions.router, dependencies=signed_in)
api_router.include_router(bulk_predictions.router, dependencies=admin_only)
api_router.include_router(uploads.router, dependencies=admin_only)
api_router.include_router(dashboard.router, dependencies=signed_in)
api_router.include_router(reviews.router, dependencies=signed_in)
api_router.include_router(duplicate_suggestions.router, dependencies=signed_in)
api_router.include_router(duplicate_queue.router, dependencies=signed_in)
api_router.include_router(model_versions.router, dependencies=signed_in)
api_router.include_router(triage.router, dependencies=signed_in)
api_router.include_router(csv_evaluation.router, dependencies=admin_only)
api_router.include_router(app_settings.router, dependencies=admin_only)
api_router.include_router(users.router, dependencies=admin_only)
