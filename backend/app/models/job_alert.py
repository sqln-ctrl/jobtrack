from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class JobAlert(Base):
    """One job recommendation found in a LinkedIn alert email."""

    __tablename__ = "job_alerts"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", "position", name="uq_job_alert_user_message_position"),
        Index("ix_job_alerts_user_received", "user_id", "received_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(64), index=True)
    gmail_thread_id: Mapped[Optional[str]] = mapped_column(String(64))
    position: Mapped[int] = mapped_column(Integer)
    job_title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    job_url: Mapped[str] = mapped_column(String(2048))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
