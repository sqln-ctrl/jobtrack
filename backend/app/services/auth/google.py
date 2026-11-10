from typing import Optional
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
LOGIN_SCOPE = "openid email profile"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def build_auth_url(*, redirect_uri: str, scope: str, state: str, offline: bool = False, login_hint: Optional[str] = None) -> str:
    params = {
        "client_id": get_settings().google_client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": scope, "state": state, "include_granted_scopes": "true",
    }
    if offline:
        params.update({"access_type": "offline", "prompt": "consent"})
    if login_hint:
        params["login_hint"] = login_hint
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    s = get_settings()
    r = httpx.post(TOKEN_URL, data={
        "code": code, "client_id": s.google_client_id, "client_secret": s.google_client_secret,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code",
    }, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_userinfo(access_token: str) -> dict:
    r = httpx.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    r.raise_for_status()
    return r.json()


def revoke_token(token: str) -> None:
    """Best effort: failing to revoke must never block a disconnect."""
    try:
        httpx.post(REVOKE_URL, data={"token": token}, timeout=10)
    except httpx.HTTPError:
        pass
