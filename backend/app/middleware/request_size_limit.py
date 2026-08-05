from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects oversized requests by Content-Length before the body is ever
    read into memory. This is a blunt, app-wide backstop — the uploads
    endpoint still enforces its own precise 25MB PDF limit after reading;
    this just stops someone from streaming an enormous body at any other
    JSON endpoint and exhausting memory before that logic ever runs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = None
            if size is not None and size > settings.max_request_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "İstek boyutu izin verilen sınırı aşıyor."},
                )
        return await call_next(request)
