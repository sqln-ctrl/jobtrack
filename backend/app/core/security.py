from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

import jwt
from cryptography.fernet import Fernet

from app.core.config import get_settings

ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(payload: dict, minutes: int) -> str:
    s = get_settings()
    return jwt.encode({**payload, "exp": _now() + timedelta(minutes=minutes)}, s.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, typ: str) -> Optional[dict]:
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return data if data.get("typ") == typ else None


def create_session_token(user_id: int) -> str:
    return _encode({"sub": str(user_id), "typ": "session"}, get_settings().session_hours * 60)


def create_state_token(purpose: str, user_id: Optional[int] = None) -> str:
    return _encode({"typ": "oauth_state", "purpose": purpose, "uid": user_id, "nonce": secrets.token_urlsafe(12)}, 10)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _fernet() -> Fernet:
    return Fernet(get_settings().token_encryption_key.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
