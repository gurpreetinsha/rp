import uuid
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import BatchStatus


class TemplateColumnInfo(BaseModel):
    name: str
    required: bool
    description: str
    example: str


class TemplateInfoOut(BaseModel):
    columns: List[TemplateColumnInfo]
    csv_sample: str


class BatchRowOut(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    row_number: int
    raw_registration_number: str
    raw_marks_obtained: Optional[str] = None
    is_absent: bool
    is_valid: bool
    validation_errors: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    course_id: uuid.UUID
    uploaded_by_teacher_id: uuid.UUID
    max_marks: float
    file_name: str
    file_hash: str
    total_rows: int
    valid_rows: int
    error_rows: int
    status: BatchStatus
    rejection_reason: Optional[str] = None
    reviewed_by_admin_id: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchDetailOut(BatchOut):
    session_name: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    teacher_name: Optional[str] = None
    sample_errors: Optional[List[Dict[str, Any]]] = None


class BatchRejectRequest(BaseModel):
    """Payload provided by an Administrator when rejecting a submitted batch."""
    reason: str = Field(..., min_length=3, max_length=500, examples=["File contains invalid roll numbers for Section B"])

