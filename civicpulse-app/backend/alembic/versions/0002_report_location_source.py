"""Module 2: remember whether the pin came from GPS or was placed by hand

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("location_source", sa.String(20), nullable=False, server_default="gps"),
    )


def downgrade() -> None:
    op.drop_column("reports", "location_source")
