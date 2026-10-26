import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------------- Teacher Schemas ----------------
class TeacherCreate(BaseModel):
    email: EmailStr = Field(..., examples=["faculty.smith@institution.edu"])
    password: str = Field(..., min_length=8, max_length=128, examples=["FacultyPass2026!"])
    full_name: str = Field(..., min_length=2, max_length=150, examples=["Dr. Alice Smith"])
    employee_id: str = Field(..., min_length=2, max_length=50, examples=["EMP1001"])
    department_id: uuid.UUID
    designation: str = Field("Assistant Professor", max_length=100)


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    employee_id: Optional[str] = Field(None, min_length=2, max_length=50)
    department_id: Optional[uuid.UUID] = None
    designation: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class TeacherOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_id: str
    department_id: uuid.UUID
    designation: str
    is_active: bool
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Student Schemas ----------------
class StudentCreate(BaseModel):
    email: EmailStr = Field(..., examples=["student.john@institution.edu"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StudentPass2026!"])
    full_name: str = Field(..., min_length=2, max_length=150, examples=["John Doe"])
    registration_number: str = Field(..., min_length=3, max_length=50, examples=["REG2026001"])
    roll_number: Optional[str] = Field(None, max_length=50, examples=["CS-26-01"])
    program_id: uuid.UUID
    current_semester: int = Field(1, ge=1, le=12)


class StudentUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    registration_number: Optional[str] = Field(None, min_length=3, max_length=50)
    roll_number: Optional[str] = Field(None, max_length=50)
    program_id: Optional[uuid.UUID] = None
    current_semester: Optional[int] = Field(None, ge=1, le=12)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class StudentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    registration_number: str
    roll_number: Optional[str] = None
    program_id: uuid.UUID
    current_semester: int
    is_active: bool
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Enrollment Schemas ----------------
class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID
    session_id: uuid.UUID


class EnrollmentBatchCreate(BaseModel):
    session_id: uuid.UUID
    course_id: uuid.UUID
    student_ids: List[uuid.UUID]


class EnrollmentOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    session_id: uuid.UUID
    is_active: bool
    registration_number: Optional[str] = None
    student_name: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Assignment Schemas ----------------
class AssignmentCreate(BaseModel):
    teacher_id: uuid.UUID
    course_id: uuid.UUID
    session_id: uuid.UUID


class AssignmentOut(BaseModel):
    id: uuid.UUID
    teacher_id: uuid.UUID
    course_id: uuid.UUID
    session_id: uuid.UUID
    is_active: bool
    teacher_name: Optional[str] = None
    employee_id: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    session_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
