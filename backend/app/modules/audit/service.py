import uuid
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog


class AuditService:
    """Central service for creating immutable audit log entries."""

    @staticmethod
    def log(
        db: Session,
        user_id: Optional[uuid.UUID],
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details,
            ip_address=ip_address,
        )
        db.add(entry)
        return entry
