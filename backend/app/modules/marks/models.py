import uuid
from typing import Optional, List
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import TimestampMixin, utcnow


class OfficialMark(Base, TimestampMixin):
    """Official academic mark for a student in a course during an examination session."""
    __tablename__ = "official_marks"
    __table_args__ = (
        sa.UniqueConstraint("session_id", "course_id", "student_id", name="uq_official_mark_session_course_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("examination_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("mark_import_batches.id", ondelete="RESTRICT"), nullable=False
    )
    marks_obtained: Mapped[float] = mapped_column(sa.Float, nullable=False)
    max_marks: Mapped[float] = mapped_column(sa.Float, nullable=False)
    is_absent: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    is_amended: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    session: Mapped["ExaminationSession"] = relationship("ExaminationSession", back_populates="official_marks")
    course: Mapped["Course"] = relationship("Course", back_populates="official_marks")
    student: Mapped["Student"] = relationship("Student", back_populates="official_marks")
    batch: Mapped["MarkImportBatch"] = relationship("MarkImportBatch", back_populates="official_marks")
    amendments: Mapped[List["MarkAmendment"]] = relationship(
        "MarkAmendment", back_populates="official_mark", cascade="all, delete-orphan"
    )


class MarkAmendment(Base):
    """Audited post-publication mark correction history."""
    __tablename__ = "mark_amendments"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    official_mark_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("official_marks.id", ondelete="CASCADE"), nullable=False
    )
    old_marks_obtained: Mapped[float] = mapped_column(sa.Float, nullable=False)
    new_marks_obtained: Mapped[float] = mapped_column(sa.Float, nullable=False)
    old_is_absent: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    new_is_absent: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    amended_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )

    official_mark: Mapped["OfficialMark"] = relationship("OfficialMark", back_populates="amendments")
