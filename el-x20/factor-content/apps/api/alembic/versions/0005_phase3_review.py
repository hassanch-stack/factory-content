"""Phase 3: índices de soporte para Review (audit_logs por entidad,
content_items por status ya existía desde 0002 y cubre la cola de review)

Revision ID: 0005
Revises: 0004
Create Date: Phase 3
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
