from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt, encrypt
from app.models.enums import SyncStatus
from app.models.gmail import GmailConnection
from app.services.auth.google import TOKEN_URL
from app.services.gmail.client import GmailAuthError, GmailError

REVOKED_MESSAGE = "Gmail access expired or was revoked. Reconnect Gmail to resume syncing."


def get_valid_access_token(db: Session, conn: GmailConnection) -> str:
    now = datetime.now(timezone.utc)
    expiry = conn.token_expiry
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry and expiry > now + timedelta(seconds=60):
        return decrypt(conn.encrypted_access_token)

    if not conn.encrypted_refresh_token:
        _mark_revoked(db, conn)
        raise GmailAuthError(REVOKED_MESSAGE)
    s = get_settings()
    resp = httpx.post(TOKEN_URL, data={
        "client_id": s.google_client_id, "client_secret": s.google_client_secret,
        "refresh_token": decrypt(conn.encrypted_refresh_token), "grant_type": "refresh_token",
    }, timeout=15)
    if resp.status_code in (400, 401):  # invalid_grant: user revoked access or token expired
        _mark_revoked(db, conn)
        raise GmailAuthError(REVOKED_MESSAGE)
    if resp.status_code != 200:
        raise GmailError(f"Token refresh failed ({resp.status_code})")
    data = resp.json()
    conn.encrypted_access_token = encrypt(data["access_token"])
    conn.token_expiry = now + timedelta(seconds=int(data.get("expires_in", 3600)))
    db.commit()
    return data["access_token"]


def _mark_revoked(db: Session, conn: GmailConnection) -> None:
    conn.sync_status = SyncStatus.REVOKED.value
    conn.last_error = REVOKED_MESSAGE
    db.commit()
