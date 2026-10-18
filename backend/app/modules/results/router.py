import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.enums import ResultStatus
from app.modules.auth.dependencies import require_admin, require_staff
from app.modules.auth.models import User
from app.modules.results.schemas import (
    CalculatedResultOut,
    CalculationSummaryOut,
    CalculateRequest,
    WithholdRequest,
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
    return ResultsService.list_session_results(
        db=db,
        session_id=session_id,
        result_status=result_status,
        is_withheld=is_withheld,
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
