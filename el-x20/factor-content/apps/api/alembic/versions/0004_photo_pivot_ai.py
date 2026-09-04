"""Pivote a fotos: script_templates + ai_generations

Revision ID: 0004
Revises: 0003
Create Date: Post-pivote vídeo->foto
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "script_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("configuration_json", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ai_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_items.id"), nullable=False),
        sa.Column("script_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("script_templates.id"), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("output_json", postgresql.JSONB, nullable=False),
        sa.Column("edited_by_user", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_generations_source_content", "ai_generations", ["source_content_id"])

    # asset_type ahora usa valores tipo photo (original_photo, rendered_photo,
    # logo...) en vez de video/thumbnail — es un string libre, no requiere
    # cambio de columna, solo se documenta aquí el cambio de convención.


def downgrade() -> None:
    op.drop_index("ix_ai_generations_source_content", table_name="ai_generations")
    op.drop_table("ai_generations")
    op.drop_table("script_templates")
