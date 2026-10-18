import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import require_staff
from app.modules.marks.schemas import OfficialMarkOut
from app.modules.marks.service import MarksService

router = APIRouter(prefix="/marks", tags=["Official Marks"])


@router.get("/official", response_model=List[OfficialMarkOut])
def list_official_marks(
    session_id: uuid.UUID = Query(..., description="Target examination session ID"),
    course_id: Optional[uuid.UUID] = Query(None, description="Filter by course ID"),
    student_id: Optional[uuid.UUID] = Query(None, description="Filter by student ID"),
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Staff-only: view official imported marks for an examination session and course."""
    return MarksService.list_official_marks(
        db=db,
        session_id=session_id,
        course_id=course_id,
        student_id=student_id,
    )


@router.get("/official/{mark_id}", response_model=OfficialMarkOut)
def get_official_mark_by_id(
    mark_id: uuid.UUID,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Staff-only: retrieve an official mark record by ID."""
    return MarksService.get_official_mark(db, mark_id)
