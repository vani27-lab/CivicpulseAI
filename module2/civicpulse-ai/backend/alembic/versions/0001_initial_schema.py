"""Module 1: initial schema (5 tables + PostGIS)

Revision ID: 0001
Revises:
Create Date: 2026-11-26
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="citizen"),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(20), nullable=False, server_default="unclassified"),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_accuracy_m", sa.Float(), nullable=True),
        sa.Column(
            "location", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
        ),
        sa.Column("severity", sa.SmallInteger(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("needs_officer_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_demo_result", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("priority_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("priority_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("priority_explanation", sa.Text(), nullable=True),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted"),
        sa.Column(
            "assigned_officer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("before_photo_path", sa.String(500), nullable=True),
        sa.Column("after_photo_path", sa.String(500), nullable=True),
        sa.Column("image_sha256", sa.String(64), nullable=True),
        sa.Column("image_embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_complaints_location", "complaints", ["location"], postgresql_using="gist")
    op.create_index("ix_complaints_category_status", "complaints", ["category", "status"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "complaint_id",
            sa.Integer(),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "citizen_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("description_original", sa.Text(), nullable=True),
        sa.Column("description_language", sa.String(5), nullable=True),
        sa.Column("description_english", sa.Text(), nullable=True),
        sa.Column("used_voice_input", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("image_sha256", sa.String(64), nullable=True),
        sa.Column("image_embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_accuracy_m", sa.Float(), nullable=True),
        sa.Column(
            "location", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
        ),
        sa.Column("duplicate_status", sa.String(20), nullable=False, server_default="none"),
        sa.Column("image_similarity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index("ix_reports_complaint_id", "reports", ["complaint_id"])
    op.create_index("ix_reports_citizen_id", "reports", ["citizen_id"])
    op.create_index("ix_reports_image_sha256", "reports", ["image_sha256"])
    op.create_index("ix_reports_location", "reports", ["location"], postgresql_using="gist")

    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "complaint_id",
            sa.Integer(),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "changed_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index("ix_status_history_complaint_id", "status_history", ["complaint_id"])


def downgrade() -> None:
    op.drop_table("status_history")
    op.drop_table("reports")
    op.drop_table("complaints")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
    # The PostGIS extension is left installed on purpose.
