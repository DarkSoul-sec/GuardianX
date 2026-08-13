from contextlib import asynccontextmanager

from fastapi import FastAPI

# IMPORTANT: Import all SQLAlchemy models before the app starts.
from app.database import models  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.findings import router as findings_router
from app.api.v1.assets import router as assets_router
from app.api.v1.auth import router as auth_router
from app.api.v1.scans import router as scans_router
from app.api.v1.users import router as users_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.activity import router as activity_router
from app.api.v1.soc import router as soc_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.virustotal import router as virustotal_router
from app.api.v1.intelligence import router as intelligence_router
from app.intelligence.router import router as intelligence_platform_router
from app.api.v1.phishing import router as phishing_router
from app.api.v1.threat_intel import router as threat_intel_router
from app.api.v1.security import router as security_router
from app.integrations.virustotal.router import router as virustotal_integration_router
from app.core.config import settings
from app.core.exceptions import (
    register_exception_handlers,
    unhandled_exception_handler,
)
from app.logger import logger
from app.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.services.mail_service import email_mode, validate_email_config
from app.tasks.scan_worker import scan_executor
from app.tasks.schedule_worker import schedule_loop
from app.tasks.intelligence_worker import shutdown as shutdown_intelligence_worker
from app.ws.hub import scan_event_hub

_WEAK_SECRET_KEYS = {
    "change-me",
    "changeme",
    "secret",
    "secret-key",
    "your-secret-key",
    "please-change-me",
    "change_me",
    "super-secret-key",
    "supersecretkey",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    secret_key = settings.SECRET_KEY.get_secret_value()

    if (
        not secret_key
        or len(secret_key) < 16
        or secret_key.lower() in _WEAK_SECRET_KEYS
    ):
        message = (
            "SECRET_KEY is missing, short, or a known placeholder. "
            "Set a strong random SECRET_KEY in .env before deploying."
        )

        if not settings.DEBUG:
            raise RuntimeError(message)

        logger.warning(message)

    if settings.ALLOW_PRIVATE_NETWORK_SCANS:
        logger.warning(
            "[DEV MODE] ALLOW_PRIVATE_NETWORK_SCANS=true — private, loopback "
            "and reserved address scan validation is bypassed. Never enable "
            "this in a public deployment."
        )

    try:
        validate_email_config(settings)
    except (RuntimeError, ValueError) as exc:
        if not settings.DEBUG:
            raise
        logger.warning("Email configuration problem: %s", exc)
    else:
        logger.info("Email delivery mode: %s", email_mode())

    import asyncio

    scan_event_hub.bind_loop(asyncio.get_running_loop())

    schedule_stop = asyncio.Event()
    scheduler_task = asyncio.create_task(
        schedule_loop(schedule_stop),
    )

    yield

    schedule_stop.set()
    await scheduler_task

    scan_executor.shutdown()
    shutdown_intelligence_worker()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Personal Cyber Defense Platform",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    exception_handlers={
        Exception: unhandled_exception_handler,
    },
)
register_exception_handlers(app)

app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.RATE_LIMIT_ENABLED,
    per_minute=settings.RATE_LIMIT_PER_MINUTE,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGIN_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    auth_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    users_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    assets_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    scans_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    reports_router,
    prefix=settings.API_PREFIX,
)
app.include_router(
    findings_router,
    prefix=settings.API_PREFIX,
)
app.include_router(dashboard_router, prefix="/api")
app.include_router(
    copilot_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    notifications_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    activity_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    soc_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    schedules_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    virustotal_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    intelligence_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    intelligence_platform_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    virustotal_integration_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    phishing_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    threat_intel_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    security_router,
    prefix=settings.API_PREFIX,
)

@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "Running",
    }


@app.get("/health")
def health():
    from app.scanners.nmap.scanner import nmap_available

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "scanner": {
            "nmap": nmap_available(),
        },
    }
