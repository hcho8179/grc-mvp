import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routes import admin, api, auth

_settings = get_settings()
if _settings.sentry_dsn:
    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.jobs import worker_loop
    task = asyncio.create_task(worker_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


from app.limiter import limiter

app = FastAPI(title="Greenlight", version="0.1.0", lifespan=lifespan)
async def _json_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many attempts. Please wait a moment and try again."},
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _json_rate_limit_handler)

# CSRF double-submit cookie validation for mutating API requests
_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
    "/api/auth/request-password-reset",
    "/api/auth/reset-password",
    "/api/auth/verify-email",
    "/api/invite/accept",          # prefix match handled below
}

@app.middleware("http")
async def enforce_csrf(request: Request, call_next):
    if _settings.testing:
        return await call_next(request)
    path = request.url.path
    is_exempt = path in _CSRF_EXEMPT_PATHS or path.startswith("/api/invite/")
    if request.method not in _CSRF_SAFE_METHODS and not is_exempt:
        cookie_token = request.cookies.get("greenlight_csrf", "")
        header_token = request.headers.get("X-CSRF-Token", "")
        if not cookie_token or not header_token or cookie_token != header_token:
            return JSONResponse({"detail": "CSRF token missing or invalid."}, status_code=403)
    return await call_next(request)


# Security headers on every response
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent browsers from MIME-sniffing the content type
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Block this site from being embedded in iframes on other domains (clickjacking)
    response.headers["X-Frame-Options"] = "DENY"
    # Don't send the full URL to third-party sites in the Referer header
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Disable browser features this app never needs
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Content Security Policy — restrict what the browser is allowed to load
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "   # React uses inline styles
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"               # modern equivalent of X-Frame-Options
    )
    if _settings.https_only:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

_origins = [o.strip() for o in _settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)             # Auth: register, login, me
app.include_router(api.router)              # JSON API for React frontend
app.include_router(admin.router, prefix="/admin", tags=["admin"])
