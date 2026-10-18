import uuid
from typing import Optional, List, Any
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import TimestampMixin
from app.core.enums import BatchStatus


class MarkImportBatch(Base, TimestampMixin):
    """Mark upload batch staged for validation, review, and approval."""
    __tablename__ = "mark_import_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("examination_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    uploaded_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )
    # Teacher specifies maximum marks for the uploaded CSV batch
    max_marks: Mapped[float] = mapped_column(sa.Float, nullable=False)
    file_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(sa.String(64), index=True, nullable=False)
    total_rows: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    error_rows: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        sa.Enum(BatchStatus, name="batch_status_enum"),
        default=BatchStatus.UPLOADING,
        nullable=False,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    reviewed_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    session: Mapped["ExaminationSession"] = relationship("ExaminationSession", back_populates="import_batches")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="uploaded_batches")
    staged_rows: Mapped[List["MarkImportRow"]] = relationship(
        "MarkImportRow", back_populates="batch", cascade="all, delete-orphan"
    )
    official_marks: Mapped[List["OfficialMark"]] = relationship("OfficialMark", back_populates="batch")


class MarkImportRow(Base, TimestampMixin):
    """Individual row staged from an uploaded marks CSV file."""
    __tablename__ = "mark_import_rows"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("mark_import_batches.id", ondelete="CASCADE"), nullable=False
    )
    row_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    raw_registration_number: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    raw_marks_obtained: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)
    is_absent: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    is_valid: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    validation_errors: Mapped[Optional[Any]] = mapped_column(sa.JSON, nullable=True)

    batch: Mapped["MarkImportBatch"] = relationship("MarkImportBatch", back_populates="staged_rows")
