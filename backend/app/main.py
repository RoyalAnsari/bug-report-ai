import logging
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import Settings
from app.core.headers import apply_security_headers
from app.repositories import app_settings as settings_repo
from app.services.app_settings import apply_to_state, build_defaults, merge_with_defaults

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bug_report_api")

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def create_app(settings=None):
    settings = settings or Settings.from_env()
    settings.validate_for_startup()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.severity = None
        app.state.finder = None
        app.state.db = None
        app.state.defaults = build_defaults(settings)
        client = None
        if settings.mongodb_uri:
            from app.db.mongo import create_client

            client = create_client(settings.mongodb_uri)
            app.state.db = client[settings.mongodb_db]
            logger.info("MongoDB client ready.")
        if settings.load_models:
            from app.ml.inference import DuplicateFinder, SeverityPredictor

            logger.info("Loading models (this can take about 30 seconds)...")
            effective = settings
            if settings.severity_model == "transformer":
                from app.ml.transformer_inference import TransformerSeverityPredictor

                app.state.severity = TransformerSeverityPredictor.from_artifact(
                    review_margin=settings.transformer_review_margin
                )
                # Settings page ka default margin transformer ke apne margin se shuru hota hai.
                effective = replace(settings, review_margin=app.state.severity.review_margin)
                logger.info("Severity model: transformer (%s)", app.state.severity.version)
            else:
                app.state.severity = SeverityPredictor.from_artifact(review_margin=settings.review_margin)
                logger.info("Severity model: TF-IDF")
            app.state.finder = DuplicateFinder.from_artifacts()
            logger.info("Models loaded.")
            app.state.defaults = build_defaults(effective, app.state.finder)
        if app.state.db is not None and (app.state.severity is not None or app.state.finder is not None):
            try:
                saved = await settings_repo.get_saved(app.state.db)
                apply_to_state(app.state, merge_with_defaults(app.state.defaults, saved))
                logger.info("Saved settings applied.")
            except Exception as error:  # the app still works with its default values
                logger.warning("Could not load the saved settings (%s). Default values are used.", type(error).__name__)
        yield
        if client is not None:
            await client.close()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.state.config = settings
    if settings.auth_enabled:
        logger.info("Authentication is ON.")
    else:
        logger.warning("Authentication is OFF (AUTH_ENABLED=false). Use this only for development.")
    if settings.enable_docs:
        logger.warning("API docs are ON (ENABLE_DOCS=true). Turn them off in production.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        apply_security_headers(response.headers, request.url.path, settings.enable_hsts)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.status_code, "message": str(exc.detail)}},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": {"code": 422, "message": "Invalid request", "details": details}},
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": 500, "message": "Internal server error"}},
        )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
