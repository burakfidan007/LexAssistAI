from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Helmet-equivalent for this FastAPI backend — a pure JSON API with no
    server-rendered HTML, so the CSP can be maximally strict (nothing is
    ever meant to load a script/style/frame from this origin)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        if settings.is_production:
            # Only meaningful once actually served over HTTPS.
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        return response
