import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import ResultStatus


class ResultSubjectDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    course_code: str
    course_name: str
    credits: float
    marks_obtained: float
    max_marks: float
    percentage: float
    is_absent: bool
    is_passed: bool
    remarks: Optional[str] = None


class CalculatedResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    registration_number: Optional[str] = None
    student_name: Optional[str] = None
    program_code: Optional[str] = None
    program_name: Optional[str] = None
    total_marks_obtained: float
    total_max_marks: float
    percentage: float
    result_status: ResultStatus
    is_withheld: bool
    calculated_at: datetime
    subject_details: Optional[List[ResultSubjectDetailOut]] = None


class CalculationSummaryOut(BaseModel):
    session_id: uuid.UUID
    session_name: str
    academic_year: str
    semester_number: int
    status: str
    total_students_enrolled: int
    total_students_evaluated: int
    total_passed: int
    total_failed: int
    total_withheld: int
    overall_pass_percentage: float
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float


class CalculateRequest(BaseModel):
    allow_partial: bool = Field(
        default=False,
        description="If True, allows calculation even if some student course enrollments lack official marks.",
    )


class WithholdRequest(BaseModel):
    is_withheld: bool = Field(..., description="Set to True to withhold the result, False to release.")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for withholding or releasing.")
