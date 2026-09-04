"""Phase 1: sources, source_checks, content_items, media_assets + índices críticos

Revision ID: 0002
Revises: 0001
Create Date: Phase 1
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("external_identifier", sa.String(255), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("permission_status", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("polling_interval", sa.Integer, nullable=False, server_default="300"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "source_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("items_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ok"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_checks_source_checked", "source_checks", ["source_id", "checked_at"])

    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("factor_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="DISCOVERED"),
        sa.Column("rights_status", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_content_items_status", "content_items", ["status"])
    op.create_index("ix_content_items_source_published", "content_items", ["source_id", "published_at"])

    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_items.id"), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("asset_type", sa.String(30), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("media_assets")
    op.drop_index("ix_content_items_source_published", table_name="content_items")
    op.drop_index("ix_content_items_status", table_name="content_items")
    op.drop_table("content_items")
    op.drop_index("ix_source_checks_source_checked", table_name="source_checks")
    op.drop_table("source_checks")
    op.drop_table("sources")
