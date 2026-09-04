"""Phase 2: templates, render_jobs

Revision ID: 0003
Revises: 0002
Create Date: Phase 2
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("configuration_json", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "render_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_items.id"), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("template_version", sa.Integer, nullable=False),
        sa.Column("input_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media_assets.id"), nullable=False),
        sa.Column("output_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media_assets.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="QUEUED"),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_render_jobs_status", "render_jobs", ["status"])
    # Acelera la comprobación de idempotencia (find_existing_succeeded_job)
    op.create_index(
        "ix_render_jobs_dedup",
        "render_jobs",
        ["content_item_id", "template_id", "template_version", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_render_jobs_dedup", table_name="render_jobs")
    op.drop_index("ix_render_jobs_status", table_name="render_jobs")
    op.drop_table("render_jobs")
    op.drop_table("templates")
