"""Aggregate import of all database models for SQLAlchemy and Alembic metadata discovery."""

from app.core.enums import UserRole, SessionStatus, BatchStatus, ResultStatus
from app.modules.auth.models import User
from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.users_mgmt.models import Student, Teacher, CourseEnrollment, TeacherCourseAssignment
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.marks.models import OfficialMark, MarkAmendment
from app.modules.results.models import CalculatedResult, ResultSubjectDetail
from app.modules.audit.models import AuditLog

__all__ = [
    "UserRole",
    "SessionStatus",
    "BatchStatus",
    "ResultStatus",
    "User",
    "Department",
    "Program",
    "Course",
    "ExaminationSession",
    "Student",
    "Teacher",
    "CourseEnrollment",
    "TeacherCourseAssignment",
    "MarkImportBatch",
    "MarkImportRow",
    "OfficialMark",
    "MarkAmendment",
    "CalculatedResult",
    "ResultSubjectDetail",
    "AuditLog",
]
