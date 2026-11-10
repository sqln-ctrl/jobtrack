from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class GmailConnection(Base):
    __tablename__ = "gmail_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    gmail_email: Mapped[str] = mapped_column(String(320))
    encrypted_access_token: Mapped[str] = mapped_column(Text)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    history_id: Mapped[Optional[str]] = mapped_column(String(64))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(16), default="idle")
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    sync_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="gmail_connection")


from app.models.user import User  # noqa: E402,F401
