import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import require_teacher, require_staff, require_admin
from app.modules.imports.schemas import (
    TemplateInfoOut, BatchOut, BatchDetailOut, BatchRowOut, BatchRejectRequest
)
from app.modules.imports.service import ImportsService

router = APIRouter(prefix="/imports", tags=["CSV Marks Upload & Validation"])


@router.get("/template", response_model=TemplateInfoOut)
def get_csv_template():
    """Retrieve the standard CSV headers, field explanations, and sample CSV layout."""
    return ImportsService.get_template_info()


@router.post("/upload", response_model=BatchDetailOut, status_code=status.HTTP_201_CREATED)
def upload_marks_csv(
    session_id: uuid.UUID = Form(..., description="ID of the target examination session"),
    course_id: uuid.UUID = Form(..., description="ID of the course being evaluated"),
    max_marks: float = Form(..., gt=0, le=1000, description="Maximum possible marks for this evaluation"),
    file: UploadFile = File(..., description="CSV file with student marks"),
    current_teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Teacher upload endpoint:
    - Accepts marks CSV and evaluation metadata.
    - Executes the 12-step validation pipeline.
    - Stages all rows into the database.
    - Sets batch status to PENDING_APPROVAL if 100% valid, or VALIDATION_FAILED if any row fails.
    """
    batch_detail, _ = ImportsService.upload_marks_csv(
        db=db,
        teacher_user=current_teacher,
        session_id=session_id,
        course_id=course_id,
        max_marks=max_marks,
        file=file,
    )
    return batch_detail


@router.get("/batches", response_model=List[BatchOut])
def list_upload_batches(
    session_id: Optional[uuid.UUID] = Query(None),
    course_id: Optional[uuid.UUID] = Query(None),
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """List uploaded batches (Administrators view all institutional batches; Teachers view only their own)."""
    return ImportsService.list_batches(
        db=db,
        current_user=current_staff,
        session_id=session_id,
        course_id=course_id,
    )


@router.get("/batches/{batch_id}", response_model=BatchDetailOut)
def get_batch_details(
    batch_id: uuid.UUID,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Retrieve full batch status, metadata, row counts, and sample validation errors."""
    return ImportsService.get_batch(db, batch_id, current_staff)


@router.get("/batches/{batch_id}/rows", response_model=List[BatchRowOut])
def get_batch_rows(
    batch_id: uuid.UUID,
    errors_only: bool = Query(False, description="Filter only rows that failed validation"),
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Retrieve row-by-row staging records for an upload batch, including line numbers and error descriptors."""
    return ImportsService.get_batch_rows(
        db=db,
        batch_id=batch_id,
        current_user=current_staff,
        errors_only=errors_only,
    )


@router.post("/batches/{batch_id}/approve", response_model=BatchDetailOut)
def approve_batch(
    batch_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: formally approve a pending batch and atomically import rows into official academic records."""
    return ImportsService.approve_batch(db, batch_id, current_admin)


@router.post("/batches/{batch_id}/reject", response_model=BatchDetailOut)
def reject_batch(
    batch_id: uuid.UUID,
    payload: BatchRejectRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: reject a mark batch with a mandatory written explanation."""
    return ImportsService.reject_batch(db, batch_id, payload.reason, current_admin)

