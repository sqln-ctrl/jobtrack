"""simplify application statuses

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11
"""
from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


STATUS_MAP = """
CASE {column}
    WHEN 'saved' THEN 'sent'
    WHEN 'applied' THEN 'sent'
    WHEN 'no_response' THEN 'sent'
    WHEN 'under_review' THEN 'viewed'
    WHEN 'assessment' THEN 'viewed'
    WHEN 'rejected' THEN 'viewed'
    WHEN 'withdrawn' THEN 'viewed'
    WHEN 'interview' THEN 'interview_call'
    WHEN 'offer' THEN 'accepted'
    ELSE {column}
END
"""


def upgrade() -> None:
    op.execute(f"UPDATE job_applications SET status = {STATUS_MAP.format(column='status')}")
    op.execute(f"UPDATE application_history SET new_status = {STATUS_MAP.format(column='new_status')}")
    op.execute(f"UPDATE application_history SET previous_status = {STATUS_MAP.format(column='previous_status')} WHERE previous_status IS NOT NULL")


def downgrade() -> None:
    # The previous status values cannot be reconstructed without losing data.
    pass
