import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import applications, auth, dashboard, emails, gmail, interviews, platforms
from app.core.config import get_settings
from app.core.cookies import CSRF_COOKIE
from app.core.errors import AppError
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = get_settings()
    if s.is_production and (not s.cookie_secure or s.secret_key.startswith("dev")):
        raise RuntimeError("Production requires COOKIE_SECURE=true and a real SECRET_KEY")
    with SessionLocal() as db:
        platforms.seed_default_platforms(db)
    yield


app = FastAPI(title="JobTrack API", version="0.3.0", lifespan=lifespan)
settings = get_settings()


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    """Double-submit CSRF check for every state-changing request."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        cookie = request.cookies.get(CSRF_COOKIE, "")
        header = request.headers.get("x-csrf-token", "")
        if not cookie or not hmac.compare_digest(cookie, header):
            return JSONResponse({"detail": "CSRF validation failed"}, status_code=403)
    return await call_next(request)


app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for module in (auth, applications, platforms, gmail, emails, dashboard, interviews):
    app.include_router(module.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
