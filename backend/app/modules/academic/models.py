import uuid
from typing import Optional, List
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import TimestampMixin
from app.core.enums import SessionStatus


class Department(Base, TimestampMixin):
    """Academic Department (e.g., Computer Science, Electrical Engineering)."""
    __tablename__ = "academic_departments"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(sa.String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    programs: Mapped[List["Program"]] = relationship("Program", back_populates="department")
    teachers: Mapped[List["Teacher"]] = relationship("Teacher", back_populates="department")


class Program(Base, TimestampMixin):
    """Academic Degree/Program (e.g., B.Tech in Computer Science, MCA)."""
    __tablename__ = "academic_programs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("academic_departments.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(sa.String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    total_semesters: Mapped[int] = mapped_column(sa.Integer, default=8, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="program")


class Course(Base, TimestampMixin):
    """Course/Subject offered by the institution (e.g., CS201 - Data Structures)."""
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(sa.String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    credits: Mapped[float] = mapped_column(sa.Float, default=3.0, nullable=False)
    pass_percentage: Mapped[float] = mapped_column(sa.Float, default=40.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    enrollments: Mapped[List["CourseEnrollment"]] = relationship("CourseEnrollment", back_populates="course")
    assignments: Mapped[List["TeacherCourseAssignment"]] = relationship("TeacherCourseAssignment", back_populates="course")
    official_marks: Mapped[List["OfficialMark"]] = relationship("OfficialMark", back_populates="course")


class ExaminationSession(Base, TimestampMixin):
    """Examination session/term (e.g., 'Spring 2026 End-Semester Examinations')."""
    __tablename__ = "examination_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    academic_year: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # e.g., "2025-2026"
    semester_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)   # e.g., 4
    status: Mapped[SessionStatus] = mapped_column(
        sa.Enum(SessionStatus, name="session_status_enum"),
        default=SessionStatus.DRAFT,
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    published_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    enrollments: Mapped[List["CourseEnrollment"]] = relationship("CourseEnrollment", back_populates="session")
    assignments: Mapped[List["TeacherCourseAssignment"]] = relationship("TeacherCourseAssignment", back_populates="session")
    import_batches: Mapped[List["MarkImportBatch"]] = relationship("MarkImportBatch", back_populates="session")
    official_marks: Mapped[List["OfficialMark"]] = relationship("OfficialMark", back_populates="session")
    calculated_results: Mapped[List["CalculatedResult"]] = relationship("CalculatedResult", back_populates="session")
