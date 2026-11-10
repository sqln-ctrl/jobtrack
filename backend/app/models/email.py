from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_email_user_message"),
        Index("ix_emails_user_received", "user_id", "received_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(64))
    gmail_thread_id: Mapped[Optional[str]] = mapped_column(String(64))
    sender: Mapped[str] = mapped_column(String(512))
    subject: Mapped[str] = mapped_column(String(998), default="")
    email_body_excerpt: Mapped[Optional[str]] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    classification: Mapped[str] = mapped_column(String(32))
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    extracted_company: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_job_title: Mapped[Optional[str]] = mapped_column(String(255))
    processing_status: Mapped[str] = mapped_column(String(16), default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    links: Mapped[list["ApplicationEmail"]] = relationship(back_populates="email", cascade="all, delete-orphan")


from app.models.application import ApplicationEmail  # noqa: E402,F401
