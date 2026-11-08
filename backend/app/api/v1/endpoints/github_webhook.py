import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.services import github_triage

logger = logging.getLogger("bug_report_api")

router = APIRouter(tags=["integrations"])


def process_issue(app, payload):
    config = app.state.config
    predictor = getattr(app.state, "severity", None)
    finder = getattr(app.state, "finder", None)
    if predictor is None or not config.github_token:
        logger.warning("GitHub issue skipped: the model or GITHUB_TOKEN is not available.")
        return
    try:
        outcome = github_triage.handle_issue_opened(payload, predictor, finder, github_triage.make_poster(config.github_token))
        logger.info("GitHub issue handled: %s", outcome)
    except Exception:
        logger.exception("GitHub issue handling failed")


@router.post("/integrations/github/webhook", status_code=202)
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """GitHub ke 'issues' webhook ke liye. Login ki jagah signature se pehchan hoti hai."""
    config = request.app.state.config
    if not config.github_webhook_secret:
        raise HTTPException(status_code=404, detail="The GitHub integration is not enabled")

    body = await request.body()
    if not github_triage.verify_signature(config.github_webhook_secret, body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "issues":
        return {"ok": True, "ignored": event or "unknown"}
    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(status_code=400, detail="The body is not valid JSON")
    if payload.get("action") != "opened":
        return {"ok": True, "ignored": f"issues:{payload.get('action')}"}

    background_tasks.add_task(process_issue, request.app, payload)
    return {"ok": True, "accepted": True}
