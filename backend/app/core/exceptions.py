"""
Domain exception hierarchy and their FastAPI exception handlers.

Services raise ``GuardianXError`` subclasses for domain-level failures
instead of generic ``Exception`` / ``ValueError`` values. A central set of
handlers (registered in ``app.main``) maps them to consistent HTTP responses
and logs them, keeping API routes thin.

Mapping:

- ``ResourceNotFoundError``     -> 404
- ``ValidationError``           -> 400
- ``ConflictError``             -> 409
- ``PermissionDeniedError``     -> 403
- ``ScanExecutionError``        -> 500
- ``ExternalServiceError``      -> 502
- any unhandled exception       -> 500 (logged, never leaked)
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("guardianx.exceptions")


class GuardianXError(Exception):
    """Base class for every domain error."""

    status_code = 500
    code = "internal_error"
    detail = "An unexpected error occurred."

    def __init__(
        self,
        detail: str | None = None,
        *,
        status_code: int | None = None,
    ) -> None:
        self.detail = detail or self.detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class ResourceNotFoundError(GuardianXError):
    """The requested resource does not exist or is not visible."""

    status_code = 404
    code = "not_found"
    detail = "The requested resource was not found."


class ValidationError(GuardianXError):
    """The request violates a domain rule or contains invalid data."""

    status_code = 400
    code = "validation_error"
    detail = "The request contains invalid data."


class ConflictError(GuardianXError):
    """The request conflicts with the current state of a resource."""

    status_code = 409
    code = "conflict"
    detail = "The request conflicts with the current resource state."


class PermissionDeniedError(GuardianXError):
    """The authenticated user cannot perform the requested action."""

    status_code = 403
    code = "permission_denied"
    detail = "You do not have permission to perform this action."


class ScanExecutionError(GuardianXError):
    """A scan pipeline step failed."""

    status_code = 500
    code = "scan_execution_error"
    detail = "The scan failed to execute."


class ExternalServiceError(GuardianXError):
    """An external dependency (NVD, AI provider, ...) failed."""

    status_code = 502
    code = "external_service_error"
    detail = "An external service could not be reached."


class APIError(GuardianXError):
    """HTTP-level error raised directly by routes.

    Carries an explicit status code and machine-readable ``code`` while
    flowing through the same single ``{detail, code}`` envelope as every
    other domain error.
    """

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        detail: str,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail
        super().__init__(detail)


_HTTP_STATUS_CODES: dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "validation_error",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


# ---------------------------------------------------------------------
# FastAPI handlers
# ---------------------------------------------------------------------


async def guardianx_exception_handler(
    request: Request,
    exc: GuardianXError,
) -> JSONResponse:
    """Map domain errors to JSON responses and log them appropriately."""

    if exc.status_code >= 500:
        logger.exception(
            "%s: %s",
            exc.code,
            exc.detail,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
    else:
        logger.warning(
            "%s: %s",
            exc.code,
            exc.detail,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Log validation failures and return the standard FastAPI shape."""

    logger.warning(
        "Request validation failed: %s",
        json_dumps(exc.errors()),
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "code": "validation_error",
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Normalize Starlette/FastAPI ``HTTPException`` to the common envelope.

    Authentication failures must keep the ``WWW-Authenticate`` header so the
    OpenAPI security scheme and OAuth2 clients still work.
    """

    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "code": _HTTP_STATUS_CODES.get(exc.status_code, "http_error"),
        },
        headers=exc.headers,
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Map constraint violations (e.g. duplicate unique keys) to 409."""

    logger.warning(
        "Integrity constraint violated on %s %s: %s",
        request.method,
        request.url.path,
        str(exc.orig)[:300],
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "The resource already exists or is locked by another operation.",
            "code": "conflict",
        },
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Map unexpected database failures to a stable 503 without leaking details."""

    logger.exception(
        "Database error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "The database is temporarily unavailable.",
            "code": "database_unavailable",
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all that logs the full traceback without leaking internals."""

    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred.",
            "code": "internal_error",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain and fallback exception handlers to the app.

    The ``Exception`` fallback must be passed via ``exception_handlers=``
    when the ``FastAPI`` instance is constructed: Starlette's outermost
    ``ServerErrorMiddleware`` captures the 500 handler at build time, so it
    cannot be registered afterwards.
    """

    app.add_exception_handler(
        GuardianXError,
        guardianx_exception_handler,
    )
    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )
    app.add_exception_handler(
        IntegrityError,
        integrity_error_handler,
    )
    app.add_exception_handler(
        SQLAlchemyError,
        sqlalchemy_error_handler,
    )


def json_dumps(data) -> str:
    """Serialize arbitrary handler data to JSON for log records."""
    import json

    return json.dumps(data, default=str)
