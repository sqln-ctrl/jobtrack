from fastapi import Response

from app.core.config import get_settings
from app.core.security import create_session_token, new_csrf_token

SESSION_COOKIE = "session"
CSRF_COOKIE = "csrf_token"
STATE_COOKIE = "oauth_state"


def set_csrf_cookie(response: Response) -> str:
    token = new_csrf_token()
    s = get_settings()
    # Readable by JS on purpose: the SPA echoes it in X-CSRF-Token (double-submit pattern).
    response.set_cookie(CSRF_COOKIE, token, max_age=s.session_hours * 3600, samesite="lax", secure=s.cookie_secure, httponly=False)
    return token


def set_session_cookies(response: Response, user_id: int) -> None:
    s = get_settings()
    response.set_cookie(
        SESSION_COOKIE, create_session_token(user_id), max_age=s.session_hours * 3600,
        httponly=True, samesite="lax", secure=s.cookie_secure,
    )
    set_csrf_cookie(response)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)
    response.delete_cookie(CSRF_COOKIE)


def set_state_cookie(response: Response, state: str) -> None:
    s = get_settings()
    response.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True, samesite="lax", secure=s.cookie_secure)
