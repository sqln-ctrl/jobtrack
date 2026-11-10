from typing import Optional

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask
import hmac

from app.api.deps import RateLimiter, get_current_user
from app.api.v1.emails import list_page
from app.core.config import get_settings
from app.core.cookies import STATE_COOKIE, set_state_cookie
from app.core.errors import NotFound
from app.core.security import create_state_token, decode_token, decrypt, encrypt
from app.db.session import get_db
from app.models.email import Email
from app.models.enums import SyncStatus
from app.models.gmail import GmailConnection
from app.models.user import User
from app.schemas.email import EmailPage
from app.schemas.misc import GmailStatus
from app.services.auth import google
from app.services.gmail.client import GmailClient
from app.services.gmail.sync import begin_sync, run_sync_in_background

router = APIRouter(prefix="/gmail", tags=["gmail"])
sync_limiter = RateLimiter(6, 60)
connect_limiter = RateLimiter(10, 60)


def _redirect_uri() -> str:
    return f"{get_settings().backend_url}/api/v1/gmail/callback"


def _back(query: str) -> RedirectResponse:
    resp = RedirectResponse(f"{get_settings().frontend_url}/settings?{query}")
    resp.delete_cookie(STATE_COOKIE)
    return resp


@router.get("/connect", dependencies=[Depends(connect_limiter)])
def connect(user: User = Depends(get_current_user)):
    """Starts the *separate* Gmail consent flow. Read-only scope, nothing else."""
    state = create_state_token("gmail", user.id)
    url = google.build_auth_url(redirect_uri=_redirect_uri(), scope=google.GMAIL_SCOPE, state=state, offline=True, login_hint=user.email)
    resp = RedirectResponse(url)
    set_state_cookie(resp, state)
    return resp


@router.get("/callback")
def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if error or not code or not state:
        return _back("gmail=cancelled")
    payload = decode_token(state, "oauth_state")
    if (not payload or payload.get("purpose") != "gmail" or payload.get("uid") != user.id
            or not hmac.compare_digest(request.cookies.get(STATE_COOKIE, ""), state)):
        return _back("gmail=invalid_state")
    try:
        tokens = google.exchange_code(code, _redirect_uri())
        profile = GmailClient(tokens["access_token"]).profile()
    except Exception:
        return _back("gmail=failed")
    if google.GMAIL_SCOPE not in tokens.get("scope", "").split():
        return _back("gmail=scope_denied")

    conn = db.scalar(select(GmailConnection).where(GmailConnection.user_id == user.id))
    refresh = tokens.get("refresh_token")
    if conn is None:
        if not refresh:
            return _back("gmail=failed")
        conn = GmailConnection(user_id=user.id, gmail_email=profile.get("emailAddress", user.email),
                               encrypted_access_token="", encrypted_refresh_token=encrypt(refresh))
        db.add(conn)
    elif refresh:
        conn.encrypted_refresh_token = encrypt(refresh)
    conn.gmail_email = profile.get("emailAddress", conn.gmail_email)
    conn.encrypted_access_token = encrypt(tokens["access_token"])
    conn.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
    conn.history_id = None  # forces a fresh full sync
    conn.sync_status = SyncStatus.IDLE.value
    conn.last_error = None
    db.commit()

    resp = _back("gmail=connected")
    resp.background = BackgroundTask(_initial_sync, user.id)  # initial synchronisation after connecting
    return resp


def _initial_sync(user_id: int) -> None:
    from app.db.session import SessionLocal
    with SessionLocal() as db:
        try:
            begin_sync(db, user_id)
        except Exception:
            return
    run_sync_in_background(user_id)


@router.get("/status", response_model=GmailStatus)
def status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conn = db.scalar(select(GmailConnection).where(GmailConnection.user_id == user.id))
    if conn is None:
        return GmailStatus(connected=False)
    return GmailStatus(connected=True, gmail_email=conn.gmail_email, sync_status=conn.sync_status, last_synced_at=conn.last_synced_at, last_error=conn.last_error)


@router.post("/sync", status_code=202, dependencies=[Depends(sync_limiter)])
def sync_now(background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    begin_sync(db, user.id)
    background.add_task(run_sync_in_background, user.id)
    return {"status": "syncing"}


@router.get("/emails", response_model=EmailPage)
def gmail_emails(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_page(db, user, None, None, None, page, page_size)


@router.post("/disconnect", status_code=204)
def disconnect(delete_emails: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conn = db.scalar(select(GmailConnection).where(GmailConnection.user_id == user.id))
    if conn is None:
        raise NotFound("Gmail is not connected")
    token = decrypt(conn.encrypted_refresh_token) if conn.encrypted_refresh_token else None
    db.delete(conn)  # tokens are deleted from our database whether or not Google's revoke call succeeds
    if delete_emails:
        db.execute(delete(Email).where(Email.user_id == user.id))
    db.commit()
    if token:
        google.revoke_token(token)
