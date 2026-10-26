import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.enums import ResultStatus, UserRole
from app.core.exceptions import ForbiddenException
from app.modules.auth.dependencies import require_admin, require_staff, require_student
from app.modules.auth.models import User
from app.modules.users_mgmt.models import Teacher, TeacherCourseAssignment, CourseEnrollment
from app.modules.results.schemas import (
    CalculatedResultOut,
    CalculationSummaryOut,
    CalculateRequest,
    WithholdRequest,
    StudentMarksheetOut,
)
from app.modules.results.service import ResultsService

router = APIRouter(prefix="/results", tags=["Academic Results & Calculations"])


@router.post(
    "/sessions/{session_id}/calculate",
    response_model=CalculationSummaryOut,
    status_code=status.HTTP_200_OK,
)
def calculate_session_results(
    session_id: uuid.UUID,
    payload: CalculateRequest = CalculateRequest(),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Trigger the academic calculation engine for all student enrollments in an examination session (Admin only)."""
    return ResultsService.calculate_session_results(
        db=db,
        session_id=session_id,
        current_user_id=current_admin.id,
        allow_partial=payload.allow_partial,
    )


@router.get(
    "/sessions/{session_id}/summary",
    response_model=CalculationSummaryOut,
)
def get_session_summary(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff),
):
    """View overall statistics and pass percentage metrics for an examination session (Admin & Teachers)."""
    return ResultsService.get_session_summary(db=db, session_id=session_id)


@router.get(
    "/sessions/{session_id}/students",
    response_model=List[CalculatedResultOut],
)
def list_session_results(
    session_id: uuid.UUID,
    result_status: Optional[ResultStatus] = Query(None, description="Filter by PASS or FAIL"),
    is_withheld: Optional[bool] = Query(None, description="Filter by withheld status"),
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff),
):
    """List calculated student results for an examination session (Admin & Teachers)."""
    teacher_id = None
    if current_staff.role == UserRole.TEACHER:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_staff.id).first()
        if not teacher:
            raise ForbiddenException("Teacher profile not found")
        teacher_id = teacher.id

    return ResultsService.list_session_results(
        db=db,
        session_id=session_id,
        result_status=result_status,
        is_withheld=is_withheld,
        teacher_id=teacher_id,
    )


@router.get(
    "/sessions/{session_id}/students/{student_id}",
    response_model=CalculatedResultOut,
)
def get_student_result(
    session_id: uuid.UUID,
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff),
):
    """View full subject breakdown for an individual student (Admin & Teachers)."""
    if current_staff.role == UserRole.TEACHER:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_staff.id).first()
        if not teacher:
            raise ForbiddenException("Teacher profile not found")
        assigned_courses = db.query(TeacherCourseAssignment.course_id).filter(
            TeacherCourseAssignment.teacher_id == teacher.id,
            TeacherCourseAssignment.session_id == session_id,
        ).all()
        assigned_course_ids = [c[0] for c in assigned_courses]
        if not assigned_course_ids:
            raise ForbiddenException("You are not assigned to evaluate any courses for this session")
        student_enrolled = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.session_id == session_id,
            CourseEnrollment.course_id.in_(assigned_course_ids),
        ).first()
        if not student_enrolled:
            raise ForbiddenException("You are not authorized to view results for this student")

    return ResultsService.get_student_result(
        db=db,
        session_id=session_id,
        student_id=student_id,
    )


@router.patch(
    "/{result_id}/withhold",
    response_model=CalculatedResultOut,
)
def set_result_withhold(
    result_id: uuid.UUID,
    payload: WithholdRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Withhold or release an individual student result (Admin only)."""
    return ResultsService.set_withheld_status(
        db=db,
        result_id=result_id,
        is_withheld=payload.is_withheld,
        reason=payload.reason,
        current_user_id=current_admin.id,
    )


@router.post(
    "/sessions/{session_id}/publish",
    response_model=CalculationSummaryOut,
)
def publish_session_results(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Officially publish calculated examination results making them accessible to students (Admin only)."""
    return ResultsService.publish_session_results(
        db=db,
        session_id=session_id,
        admin_user_id=current_admin.id,
    )


@router.post(
    "/sessions/{session_id}/unpublish",
    response_model=CalculationSummaryOut,
)
def unpublish_session_results(
    session_id: uuid.UUID,
    payload: WithholdRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Rollback published results to CALCULATED status for administrative correction (Admin only)."""
    return ResultsService.unpublish_session_results(
        db=db,
        session_id=session_id,
        reason=payload.reason or "Administrative rollback",
        admin_user_id=current_admin.id,
    )


@router.get(
    "/my-results",
    response_model=List[StudentMarksheetOut],
)
def get_my_published_results(
    db: Session = Depends(get_db),
    current_student_user: User = Depends(require_student),
):
    """View all officially published session marksheets for the authenticated student (Student only)."""
    return ResultsService.get_student_marksheets(
        db=db,
        student_user_id=current_student_user.id,
    )


@router.get(
    "/my-results/sessions/{session_id}",
    response_model=StudentMarksheetOut,
)
def get_my_session_result(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_student_user: User = Depends(require_student),
):
    """View official published marksheet for a specific examination session (Student only)."""
    marksheets = ResultsService.get_student_marksheets(
        db=db,
        student_user_id=current_student_user.id,
        session_id=session_id,
    )
    if not marksheets:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Published marksheet not found for this examination session")
    return marksheets[0]

