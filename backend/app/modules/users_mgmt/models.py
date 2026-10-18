import uuid
from typing import Optional, List
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.models_base import TimestampMixin


class Student(Base, TimestampMixin):
    """Student academic profile linked 1:1 to a user account."""
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    registration_number: Mapped[str] = mapped_column(
        sa.String(50), unique=True, index=True, nullable=False
    )
    roll_number: Mapped[Optional[str]] = mapped_column(sa.String(50), nullable=True)
    program_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("academic_programs.id", ondelete="RESTRICT"), nullable=False
    )
    current_semester: Mapped[int] = mapped_column(sa.Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    program: Mapped["Program"] = relationship("Program", back_populates="students")
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment", back_populates="student", cascade="all, delete-orphan"
    )
    official_marks: Mapped[List["OfficialMark"]] = relationship("OfficialMark", back_populates="student")
    calculated_results: Mapped[List["CalculatedResult"]] = relationship("CalculatedResult", back_populates="student")


class Teacher(Base, TimestampMixin):
    """Teacher faculty profile linked 1:1 to a user account."""
    __tablename__ = "teachers"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        sa.String(50), unique=True, index=True, nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("academic_departments.id", ondelete="RESTRICT"), nullable=False
    )
    designation: Mapped[str] = mapped_column(sa.String(100), default="Assistant Professor", nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")
    department: Mapped["Department"] = relationship("Department", back_populates="teachers")
    assignments: Mapped[List["TeacherCourseAssignment"]] = relationship(
        "TeacherCourseAssignment", back_populates="teacher", cascade="all, delete-orphan"
    )
    uploaded_batches: Mapped[List["MarkImportBatch"]] = relationship("MarkImportBatch", back_populates="teacher")


class CourseEnrollment(Base, TimestampMixin):
    """Enrollment mapping a student to a course for an examination session."""
    __tablename__ = "course_enrollments"
    __table_args__ = (
        sa.UniqueConstraint("student_id", "course_id", "session_id", name="uq_student_course_session"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("examination_sessions.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    session: Mapped["ExaminationSession"] = relationship("ExaminationSession", back_populates="enrollments")


class TeacherCourseAssignment(Base, TimestampMixin):
    """Assignment mapping a teacher to a course for an examination session."""
    __tablename__ = "teacher_course_assignments"
    __table_args__ = (
        sa.UniqueConstraint("teacher_id", "course_id", "session_id", name="uq_teacher_course_session"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("examination_sessions.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="assignments")
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
    session: Mapped["ExaminationSession"] = relationship("ExaminationSession", back_populates="assignments")
