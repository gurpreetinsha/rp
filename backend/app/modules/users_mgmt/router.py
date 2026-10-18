import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import (
    require_admin, require_teacher, require_student, require_staff, get_current_user
)
from app.modules.users_mgmt.schemas import (
    TeacherCreate, TeacherOut,
    StudentCreate, StudentOut,
    EnrollmentCreate, EnrollmentOut,
    AssignmentCreate, AssignmentOut,
)
from app.modules.users_mgmt.service import UsersManagementService
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter(prefix="/users-mgmt", tags=["Student & Teacher Management"])


# ---------------- Teacher Endpoints ----------------
@router.post("/teachers", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
def create_teacher(
    data: TeacherCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: register a faculty member with credentials and departmental affiliation."""
    return UsersManagementService.create_teacher(db, data)


@router.get("/teachers", response_model=List[TeacherOut])
def list_teachers(
    department_id: Optional[uuid.UUID] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list all faculty members."""
    return UsersManagementService.list_teachers(db, department_id=department_id)


@router.get("/teachers/me/assignments", response_model=List[AssignmentOut])
def get_my_assignments(
    current_teacher_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher self-view: list only the courses and examination sessions assigned to the logged-in teacher."""
    teacher = UsersManagementService.get_teacher_by_user_id(db, current_teacher_user.id)
    if not teacher:
        raise NotFoundException("Teacher profile not found for this account")
    return UsersManagementService.list_assignments(db, teacher_id=teacher.id)


@router.get("/teachers/{teacher_id}", response_model=TeacherOut)
def get_teacher_by_id(
    teacher_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: get a teacher's details by ID."""
    return UsersManagementService.get_teacher(db, teacher_id)


# ---------------- Student Endpoints ----------------
@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: register a student with credentials, registration number, and program."""
    return UsersManagementService.create_student(db, data)


@router.get("/students", response_model=List[StudentOut])
def list_students(
    program_id: Optional[uuid.UUID] = None,
    semester: Optional[int] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list students with optional program and semester filtering."""
    return UsersManagementService.list_students(db, program_id=program_id, semester=semester)


@router.get("/students/me", response_model=StudentOut)
def get_my_student_profile(
    current_student_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Student self-view: retrieve the logged-in student's academic profile."""
    student = UsersManagementService.get_student_by_user_id(db, current_student_user.id)
    if not student:
        raise NotFoundException("Student profile not found for this account")
    return UsersManagementService.get_student(db, student.id)


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student_by_id(
    student_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: get a student's profile by ID."""
    return UsersManagementService.get_student(db, student_id)


# ---------------- Enrollment Endpoints ----------------
@router.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_student(
    data: EnrollmentCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: enroll a student into a course for an examination session."""
    return UsersManagementService.enroll_student(db, data)


@router.get("/enrollments", response_model=List[EnrollmentOut])
def list_enrollments(
    session_id: Optional[uuid.UUID] = None,
    course_id: Optional[uuid.UUID] = None,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Staff (Admin/Teacher): list students enrolled in a course/session."""
    return UsersManagementService.list_enrollments(db, session_id=session_id, course_id=course_id)


# ---------------- Assignment Endpoints ----------------
@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def assign_teacher_to_course(
    data: AssignmentCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: assign a faculty member to evaluate a course in an examination session."""
    return UsersManagementService.assign_teacher(db, data)


@router.get("/assignments", response_model=List[AssignmentOut])
def list_all_assignments(
    session_id: Optional[uuid.UUID] = None,
    course_id: Optional[uuid.UUID] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list course-to-teacher assignments across the institution."""
    return UsersManagementService.list_assignments(db, session_id=session_id, course_id=course_id)
