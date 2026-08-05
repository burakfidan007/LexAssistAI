import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter
from app.db import mongo
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import activity, ai, auth, billing, cases, folders, notifications, preferences, uploads

configure_logging()
logger = logging.getLogger("lexassist.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo.connect()
    await mongo.ensure_indexes()
    yield
    mongo.disconnect()


app = FastAPI(
    title="LexAssist AI API",
    lifespan=lifespan,
    # Interactive API docs expose the full schema — fine for local dev,
    # deliberately turned off in production to reduce reconnaissance surface.
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware order matters: Starlette applies the LAST-added middleware
# OUTERMOST. CORS is added last so it wraps everything (handles preflight
# before rate limiting/size checks even run); SlowAPI is added first so it
# sits innermost, right before routing.
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serializable_validation_errors(errors: list[dict]) -> list[dict]:
    # Pydantic embeds the raw exception object (e.g. our custom
    # field_validator ValueErrors) under errors[i]["ctx"]["error"], which
    # json.dumps can't serialize on its own — stringify it explicitly
    # rather than relying on encoder fallback behavior that varies by version.
    clean = []
    for err in errors:
        err = dict(err)
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and isinstance(ctx.get("error"), BaseException):
            err["ctx"] = {**ctx, "error": str(ctx["error"])}
        clean.append(err)
    return clean


def _primary_error_message(errors: list[dict]) -> str:
    # The frontend reads `detail` directly into user-facing toasts (see
    # http.js) — surface the first field's actual message there instead of
    # a generic "validation failed", so e.g. password policy violations
    # still show the specific, actionable Turkish message they always did.
    if errors:
        msg = errors[0].get("msg")
        if isinstance(msg, str) and msg:
            return msg.removeprefix("Value error, ")
    return "Girdi doğrulama hatası."


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = _serializable_validation_errors(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": _primary_error_message(errors), "errors": errors},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internals (stack traces, exception messages) to the
    # client — log them server-side only, where an operator can see them.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."},
    )


app.include_router(auth.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(folders.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
