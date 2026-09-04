"""Phase 5: post_metrics + índice crítico

Revision ID: 0007
Revises: 0006
Create Date: Phase 5
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "post_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("views", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("likes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("comments", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("shares", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("saves", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("watch_time_ms", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("followers_gained", sa.Integer, nullable=False, server_default="0"),
        sa.Column("raw_platform_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_post_metrics_post_collected", "post_metrics", ["post_id", "collected_at"])


def downgrade() -> None:
    op.drop_index("ix_post_metrics_post_collected", table_name="post_metrics")
    op.drop_table("post_metrics")
