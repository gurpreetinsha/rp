import uuid
from typing import Optional, Any
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import utcnow


class AuditLog(Base):
    """Immutable audit trail for all critical administrative and academic changes."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(sa.String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(50), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(sa.String(100), index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(sa.String(45), nullable=True)
    details: Mapped[Optional[Any]] = mapped_column(sa.JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, index=True, nullable=False
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
