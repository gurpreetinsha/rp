import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.academic.service import AcademicService
from app.modules.academic.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentOut,
    ProgramCreate, ProgramUpdate, ProgramOut,
    CourseCreate, CourseUpdate, CourseOut,
    ExaminationSessionCreate, ExaminationSessionStatusUpdate, ExaminationSessionUpdate, ExaminationSessionOut,
)

router = APIRouter(prefix="/academic", tags=["Academic Setup"])


# ---------------- Departments ----------------
@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new academic department (Admin only)."""
    return AcademicService.create_department(db, data)


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all academic departments (Authenticated users)."""
    return AcademicService.list_departments(db, active_only=active_only)


@router.get("/departments/{department_id}", response_model=DepartmentOut)
def get_department(
    department_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific academic department by ID."""
    return AcademicService.get_department(db, department_id)


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update department details (Admin only)."""
    return AcademicService.update_department(db, department_id, data)


@router.delete("/departments/{department_id}")
def delete_department(
    department_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a department (Admin only)."""
    AcademicService.delete_department(db, department_id)
    return {"success": True, "message": "Department deleted successfully"}


# ---------------- Programs ----------------
@router.post("/programs", response_model=ProgramOut, status_code=status.HTTP_201_CREATED)
def create_program(
    data: ProgramCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new academic program under a department (Admin only)."""
    return AcademicService.create_program(db, data)


@router.get("/programs", response_model=List[ProgramOut])
def list_programs(
    department_id: Optional[uuid.UUID] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List academic programs, optionally filtered by department."""
    return AcademicService.list_programs(db, department_id=department_id, active_only=active_only)


@router.get("/programs/{program_id}", response_model=ProgramOut)
def get_program(
    program_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific program by ID."""
    return AcademicService.get_program(db, program_id)


@router.patch("/programs/{program_id}", response_model=ProgramOut)
def update_program(
    program_id: uuid.UUID,
    data: ProgramUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update program details (Admin only)."""
    return AcademicService.update_program(db, program_id, data)


@router.delete("/programs/{program_id}")
def delete_program(
    program_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an academic program (Admin only)."""
    AcademicService.delete_program(db, program_id)
    return {"success": True, "message": "Program deleted successfully"}


# ---------------- Courses ----------------
@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new course offering (Admin only)."""
    return AcademicService.create_course(db, data)


@router.get("/courses", response_model=List[CourseOut])
def list_courses(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all available courses."""
    return AcademicService.list_courses(db, active_only=active_only)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a course by ID."""
    return AcademicService.get_course(db, course_id)


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update course attributes (Admin only)."""
    return AcademicService.update_course(db, course_id, data)


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a course (Admin only)."""
    AcademicService.delete_course(db, course_id)
    return {"success": True, "message": "Course deleted successfully"}


# ---------------- Examination Sessions ----------------
@router.post("/sessions", response_model=ExaminationSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    data: ExaminationSessionCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new examination session in DRAFT status (Admin only)."""
    return AcademicService.create_session(db, data)


@router.get("/sessions", response_model=List[ExaminationSessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all examination sessions."""
    return AcademicService.list_sessions(db)


@router.get("/sessions/{session_id}", response_model=ExaminationSessionOut)
def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get an examination session by ID."""
    return AcademicService.get_session(db, session_id)


@router.patch("/sessions/{session_id}/status", response_model=ExaminationSessionOut)
def update_session_status(
    session_id: uuid.UUID,
    data: ExaminationSessionStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Transition the lifecycle status of an examination session (Admin only)."""
    return AcademicService.update_session_status(db, session_id, data.status)


@router.patch("/sessions/{session_id}", response_model=ExaminationSessionOut)
def update_session(
    session_id: uuid.UUID,
    data: ExaminationSessionUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update examination session details (Admin only)."""
    return AcademicService.update_session(db, session_id, data)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an examination session (Admin only)."""
    AcademicService.delete_session(db, session_id)
    return {"success": True, "message": "Examination session deleted successfully"}
