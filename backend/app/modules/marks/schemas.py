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
