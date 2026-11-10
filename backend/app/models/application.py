from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class Platform(Base):
    __tablename__ = "platforms"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_platform_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def is_default(self) -> bool:
        return self.user_id is None


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        Index("ix_apps_user_status", "user_id", "status"),
        Index("ix_apps_user_date", "user_id", "application_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id", ondelete="RESTRICT"), index=True)
    job_title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255))
    job_description: Mapped[Optional[str]] = mapped_column(Text)
    job_url: Mapped[Optional[str]] = mapped_column(String(2048))
    company_website: Mapped[Optional[str]] = mapped_column(String(2048))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    employment_type: Mapped[Optional[str]] = mapped_column(String(32))
    salary_range: Mapped[Optional[str]] = mapped_column(String(120))
    application_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="applied")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    platform: Mapped[Platform] = relationship()
    history: Mapped[list["ApplicationHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationHistory.created_at, ApplicationHistory.id"
    )
    email_links: Mapped[list["ApplicationEmail"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="Interview.interview_date"
    )


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("job_applications.id", ondelete="CASCADE"), index=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32))
    change_source: Mapped[str] = mapped_column(String(16))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[JobApplication] = relationship(back_populates="history")


class ApplicationEmail(Base):
    __tablename__ = "application_emails"
    __table_args__ = (UniqueConstraint("application_id", "email_id", name="uq_application_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("job_applications.id", ondelete="CASCADE"), index=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), index=True)
    match_confidence: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[JobApplication] = relationship(back_populates="email_links")
    email: Mapped["Email"] = relationship(back_populates="links")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("job_applications.id", ondelete="CASCADE"), index=True)
    interview_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    interview_type: Mapped[Optional[str]] = mapped_column(String(64))
    meeting_link: Mapped[Optional[str]] = mapped_column(String(2048))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[JobApplication] = relationship(back_populates="interviews")


from app.models.email import Email  # noqa: E402,F401
