import hmac
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import RateLimiter, get_current_user
from app.core.config import get_settings
from app.core.cookies import CSRF_COOKIE, STATE_COOKIE, clear_session_cookies, set_csrf_cookie, set_session_cookies, set_state_cookie
from app.core.security import create_state_token, decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.misc import MeOut, UserOut
from app.services.auth import google

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = RateLimiter(20, 60)


def _redirect_uri() -> str:
    return f"{get_settings().backend_url}/api/v1/auth/google/callback"


def _fail(reason: str) -> RedirectResponse:
    resp = RedirectResponse(f"{get_settings().frontend_url}/login?error={reason}")
    resp.delete_cookie(STATE_COOKIE)
    return resp


@router.get("/google", dependencies=[Depends(limiter)])
def google_login():
    state = create_state_token("login")
    resp = RedirectResponse(google.build_auth_url(redirect_uri=_redirect_uri(), scope=google.LOGIN_SCOPE, state=state))
    set_state_cookie(resp, state)
    return resp


@router.get("/google/callback", dependencies=[Depends(limiter)])
def google_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None, db: Session = Depends(get_db)):
    if error or not code or not state:
        return _fail("cancelled")
    cookie = request.cookies.get(STATE_COOKIE, "")
    payload = decode_token(state, "oauth_state")
    if not payload or payload.get("purpose") != "login" or not hmac.compare_digest(cookie, state):
        return _fail("invalid_state")
    try:
        tokens = google.exchange_code(code, _redirect_uri())
        info = google.fetch_userinfo(tokens["access_token"])
    except (httpx.HTTPError, KeyError):
        return _fail("google_unavailable")
    if not info.get("email_verified", False) or not info.get("sub") or not info.get("email"):
        return _fail("unverified_email")

    user = db.scalar(select(User).where(User.google_id == info["sub"]))
    if user is None:
        user = User(google_id=info["sub"], email=info["email"], name=info.get("name") or info["email"], profile_picture=info.get("picture"))
        db.add(user)
    else:
        user.email, user.name, user.profile_picture = info["email"], info.get("name") or user.name, info.get("picture")
    db.commit()

    resp = RedirectResponse(f"{get_settings().frontend_url}/")
    set_session_cookies(resp, user.id)
    resp.delete_cookie(STATE_COOKIE)
    return resp


@router.get("/me", response_model=MeOut)
def me(request: Request, response: Response, user: User = Depends(get_current_user)):
    if not request.cookies.get(CSRF_COOKIE):
        set_csrf_cookie(response)
    return MeOut(user=UserOut.model_validate(user), gmail_connected=user.gmail_connection is not None)


@router.post("/logout", status_code=204)
def logout(response: Response):
    clear_session_cookies(response)
    response.status_code = 204
    return response
