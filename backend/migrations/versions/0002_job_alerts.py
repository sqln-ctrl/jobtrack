"""store LinkedIn job-alert listings

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=64), nullable=False),
        sa.Column("gmail_thread_id", sa.String(length=64), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("job_url", sa.String(length=2048), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "gmail_message_id", "position", name="uq_job_alert_user_message_position"),
    )
    with op.batch_alter_table("job_alerts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_job_alerts_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_alerts_gmail_message_id"), ["gmail_message_id"], unique=False)
        batch_op.create_index("ix_job_alerts_user_received", ["user_id", "received_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("job_alerts", schema=None) as batch_op:
        batch_op.drop_index("ix_job_alerts_user_received")
        batch_op.drop_index(batch_op.f("ix_job_alerts_gmail_message_id"))
        batch_op.drop_index(batch_op.f("ix_job_alerts_user_id"))
    op.drop_table("job_alerts")
