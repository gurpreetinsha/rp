import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import SessionStatus


# ---------------- Department Schemas ----------------
class DepartmentBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=30, examples=["CSE"])
    name: str = Field(..., min_length=2, max_length=150, examples=["Computer Science and Engineering"])


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=30)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    is_active: Optional[bool] = None


class DepartmentOut(DepartmentBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Program Schemas ----------------
class ProgramBase(BaseModel):
    department_id: uuid.UUID
    code: str = Field(..., min_length=2, max_length=30, examples=["BTECH_CSE"])
    name: str = Field(..., min_length=2, max_length=150, examples=["Bachelor of Technology in CSE"])
    total_semesters: int = Field(8, ge=1, le=12)


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    code: Optional[str] = Field(None, min_length=2, max_length=30)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    total_semesters: Optional[int] = Field(None, ge=1, le=12)
    is_active: Optional[bool] = None


class ProgramOut(ProgramBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Course Schemas ----------------
class CourseBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=30, examples=["CS201"])
    name: str = Field(..., min_length=2, max_length=150, examples=["Data Structures & Algorithms"])
    credits: float = Field(3.0, gt=0, le=30)
    pass_percentage: float = Field(40.0, ge=0, le=100)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=30)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    credits: Optional[float] = Field(None, gt=0, le=30)
    pass_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class CourseOut(CourseBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Examination Session Schemas ----------------
class ExaminationSessionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150, examples=["Spring 2026 Regular Examination"])
    academic_year: str = Field(..., min_length=4, max_length=20, examples=["2025-2026"])
    semester_number: int = Field(..., ge=1, le=12)


class ExaminationSessionCreate(ExaminationSessionBase):
    pass


class ExaminationSessionStatusUpdate(BaseModel):
    status: SessionStatus


class ExaminationSessionOut(ExaminationSessionBase):
    id: uuid.UUID
    status: SessionStatus
    published_at: Optional[datetime] = None
    published_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
