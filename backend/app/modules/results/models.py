import uuid
from typing import Optional, List
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import TimestampMixin, utcnow
from app.core.enums import ResultStatus


class CalculatedResult(Base, TimestampMixin):
    """Calculated overall result summary for a student in an examination session."""
    __tablename__ = "calculated_results"
    __table_args__ = (
        sa.UniqueConstraint("session_id", "student_id", name="uq_calculated_result_session_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("examination_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    total_marks_obtained: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    total_max_marks: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    percentage: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    result_status: Mapped[ResultStatus] = mapped_column(
        sa.Enum(ResultStatus, name="result_status_enum"),
        default=ResultStatus.FAIL,
        nullable=False,
    )
    is_withheld: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )

    session: Mapped["ExaminationSession"] = relationship("ExaminationSession", back_populates="calculated_results")
    student: Mapped["Student"] = relationship("Student", back_populates="calculated_results")
    subject_details: Mapped[List["ResultSubjectDetail"]] = relationship(
        "ResultSubjectDetail", back_populates="calculated_result", cascade="all, delete-orphan"
    )


class ResultSubjectDetail(Base):
    """Subject-wise breakdown belonging to a calculated result."""
    __tablename__ = "result_subject_details"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    calculated_result_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("calculated_results.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    marks_obtained: Mapped[float] = mapped_column(sa.Float, nullable=False)
    max_marks: Mapped[float] = mapped_column(sa.Float, nullable=False)
    percentage: Mapped[float] = mapped_column(sa.Float, nullable=False)
    is_absent: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    is_passed: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(sa.String(50), nullable=True)

    calculated_result: Mapped["CalculatedResult"] = relationship("CalculatedResult", back_populates="subject_details")
    course: Mapped["Course"] = relationship("Course")
