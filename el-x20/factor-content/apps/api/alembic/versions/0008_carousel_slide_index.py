"""Soporte de carrusel: slide_index en render_jobs (ejemplo del operador
reveló que los posts son de 2 slides: hook + cuerpo)

Revision ID: 0008
Revises: 0007
Create Date: Post-ejemplo carrusel
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("render_jobs", sa.Column("slide_index", sa.Integer, nullable=False, server_default="0"))
    op.drop_index("ix_render_jobs_dedup", table_name="render_jobs")
    op.create_index(
        "ix_render_jobs_dedup",
        "render_jobs",
        ["content_item_id", "template_id", "template_version", "slide_index", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_render_jobs_dedup", table_name="render_jobs")
    op.create_index(
        "ix_render_jobs_dedup",
        "render_jobs",
        ["content_item_id", "template_id", "template_version", "status"],
    )
    op.drop_column("render_jobs", "slide_index")
