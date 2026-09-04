"""Helper único de auditoría — toda acción sensible pasa por aquí, nunca
se inserta un AuditLog "a mano" en un router (spec 24/27)."""
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record(
    db: Session,
    *,
    user_id,
    action: str,
    entity_type: str,
    entity_id,
    before: dict | None = None,
    after: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
    )
    db.add(entry)
    return entry
