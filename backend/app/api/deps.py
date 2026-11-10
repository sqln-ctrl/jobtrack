import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.cookies import SESSION_COOKIE
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    data = decode_token(token, "session") if token else None
    user = db.get(User, int(data["sub"])) if data else None
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


class RateLimiter:
    """Small in-memory sliding window limiter. Swap for Redis once there is more than one process."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit, self.window = limit, window_seconds
        self.hits = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")
        q.append(now)
