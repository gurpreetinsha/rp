import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OfficialMarkOut(BaseModel):
    """Public representation of an approved, official academic mark."""
    id: uuid.UUID
    session_id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    batch_id: uuid.UUID
    marks_obtained: float
    max_marks: float
    percentage: float
    is_absent: bool
    is_amended: bool
    registration_number: Optional[str] = None
    student_name: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AmendMarkRequest(BaseModel):
    new_marks_obtained: float
    new_is_absent: bool = False
    reason: str
    requested_by_id: Optional[uuid.UUID] = None


class MarkAmendmentOut(BaseModel):
    id: uuid.UUID
    official_mark_id: uuid.UUID
    old_marks_obtained: float
    new_marks_obtained: float
    old_is_absent: bool
    new_is_absent: bool
    reason: str
    requested_by_id: uuid.UUID
    approved_by_id: uuid.UUID
    amended_at: datetime

    model_config = ConfigDict(from_attributes=True)
