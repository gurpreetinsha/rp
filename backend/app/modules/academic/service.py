import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.academic.schemas import (
    DepartmentCreate, DepartmentUpdate,
    ProgramCreate, ProgramUpdate,
    CourseCreate, CourseUpdate,
    ExaminationSessionCreate, ExaminationSessionUpdate,
)
from app.core.exceptions import NotFoundException, ConflictException
from app.core.enums import SessionStatus
from app.modules.users_mgmt.models import Teacher, Student, CourseEnrollment, TeacherCourseAssignment
from app.modules.marks.models import OfficialMark


class AcademicService:
    """Service handling business logic for academic organizational hierarchy."""

    # ---------------- Department Operations ----------------
    @staticmethod
    def create_department(db: Session, data: DepartmentCreate) -> Department:
        existing = db.execute(select(Department).where(Department.code == data.code.strip().upper())).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Department with code '{data.code}' already exists")

        dept = Department(
            code=data.code.strip().upper(),
            name=data.name.strip(),
        )
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def get_department(db: Session, department_id: uuid.UUID) -> Department:
        dept = db.get(Department, department_id)
        if not dept:
            raise NotFoundException(f"Department with ID {department_id} not found")
        return dept

    @staticmethod
    def list_departments(db: Session, active_only: bool = True) -> List[Department]:
        query = select(Department)
        if active_only:
            query = query.where(Department.is_active == True)
        return list(db.execute(query.order_by(Department.name)).scalars().all())

    @staticmethod
    def update_department(db: Session, department_id: uuid.UUID, data: DepartmentUpdate) -> Department:
        dept = AcademicService.get_department(db, department_id)
        if data.code is not None:
            new_code = data.code.strip().upper()
            existing = db.execute(select(Department).where(Department.code == new_code, Department.id != department_id)).scalar_one_or_none()
            if existing:
                raise ConflictException(f"Department with code '{new_code}' already exists")
            dept.code = new_code
        if data.name is not None:
            dept.name = data.name.strip()
        if data.is_active is not None:
            dept.is_active = data.is_active

        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def delete_department(db: Session, department_id: uuid.UUID) -> None:
        dept = AcademicService.get_department(db, department_id)
        has_programs = db.execute(select(Program).where(Program.department_id == department_id)).scalars().first()
        if has_programs:
            raise ConflictException("Cannot delete department with associated academic programs. Remove or reassign programs first.")
        has_teachers = db.execute(select(Teacher).where(Teacher.department_id == department_id)).scalars().first()
        if has_teachers:
            raise ConflictException("Cannot delete department with affiliated teachers. Remove or reassign teachers first.")
        db.delete(dept)
        db.commit()

    # ---------------- Program Operations ----------------
    @staticmethod
    def create_program(db: Session, data: ProgramCreate) -> Program:
        # Check department exists
        AcademicService.get_department(db, data.department_id)

        existing = db.execute(select(Program).where(Program.code == data.code.strip().upper())).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Program with code '{data.code}' already exists")

        prog = Program(
            department_id=data.department_id,
            code=data.code.strip().upper(),
            name=data.name.strip(),
            total_semesters=data.total_semesters,
        )
        db.add(prog)
        db.commit()
        db.refresh(prog)
        return prog

    @staticmethod
    def get_program(db: Session, program_id: uuid.UUID) -> Program:
        prog = db.get(Program, program_id)
        if not prog:
            raise NotFoundException(f"Program with ID {program_id} not found")
        return prog

    @staticmethod
    def list_programs(db: Session, department_id: Optional[uuid.UUID] = None, active_only: bool = True) -> List[Program]:
        query = select(Program)
        if department_id:
            query = query.where(Program.department_id == department_id)
        if active_only:
            query = query.where(Program.is_active == True)
        return list(db.execute(query.order_by(Program.name)).scalars().all())

    @staticmethod
    def update_program(db: Session, program_id: uuid.UUID, data: ProgramUpdate) -> Program:
        prog = AcademicService.get_program(db, program_id)
        if data.department_id is not None:
            AcademicService.get_department(db, data.department_id)
            prog.department_id = data.department_id
        if data.code is not None:
            new_code = data.code.strip().upper()
            existing = db.execute(select(Program).where(Program.code == new_code, Program.id != program_id)).scalar_one_or_none()
            if existing:
                raise ConflictException(f"Program with code '{new_code}' already exists")
            prog.code = new_code
        if data.name is not None:
            prog.name = data.name.strip()
        if data.total_semesters is not None:
            prog.total_semesters = data.total_semesters
        if data.is_active is not None:
            prog.is_active = data.is_active

        db.commit()
        db.refresh(prog)
        return prog

    @staticmethod
    def delete_program(db: Session, program_id: uuid.UUID) -> None:
        prog = AcademicService.get_program(db, program_id)
        has_students = db.execute(select(Student).where(Student.program_id == program_id)).scalars().first()
        if has_students:
            raise ConflictException("Cannot delete program with enrolled students. Remove or reassign students first.")
        db.delete(prog)
        db.commit()

    # ---------------- Course Operations ----------------
    @staticmethod
    def create_course(db: Session, data: CourseCreate) -> Course:
        existing = db.execute(select(Course).where(Course.code == data.code.strip().upper())).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Course with code '{data.code}' already exists")

        course = Course(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            credits=data.credits,
            pass_percentage=data.pass_percentage,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_course(db: Session, course_id: uuid.UUID) -> Course:
        course = db.get(Course, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} not found")
        return course

    @staticmethod
    def list_courses(db: Session, active_only: bool = True) -> List[Course]:
        query = select(Course)
        if active_only:
            query = query.where(Course.is_active == True)
        return list(db.execute(query.order_by(Course.code)).scalars().all())

    @staticmethod
    def update_course(db: Session, course_id: uuid.UUID, data: CourseUpdate) -> Course:
        course = AcademicService.get_course(db, course_id)
        if data.code is not None:
            new_code = data.code.strip().upper()
            existing = db.execute(select(Course).where(Course.code == new_code, Course.id != course_id)).scalar_one_or_none()
            if existing:
                raise ConflictException(f"Course with code '{new_code}' already exists")
            course.code = new_code
        if data.name is not None:
            course.name = data.name.strip()
        if data.credits is not None:
            course.credits = data.credits
        if data.pass_percentage is not None:
            course.pass_percentage = data.pass_percentage
        if data.is_active is not None:
            course.is_active = data.is_active

        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: uuid.UUID) -> None:
        course = AcademicService.get_course(db, course_id)
        has_marks = db.execute(select(OfficialMark).where(OfficialMark.course_id == course_id)).scalars().first()
        if has_marks:
            raise ConflictException("Cannot delete course with recorded official marks.")
        # Clean up enrollments and assignments for this course
        enrollments = db.execute(select(CourseEnrollment).where(CourseEnrollment.course_id == course_id)).scalars().all()
        for e in enrollments:
            db.delete(e)
        assignments = db.execute(select(TeacherCourseAssignment).where(TeacherCourseAssignment.course_id == course_id)).scalars().all()
        for a in assignments:
            db.delete(a)
        db.delete(course)
        db.commit()

    # ---------------- Examination Session Operations ----------------
    @staticmethod
    def create_session(db: Session, data: ExaminationSessionCreate) -> ExaminationSession:
        session = ExaminationSession(
            name=data.name.strip(),
            academic_year=data.academic_year.strip(),
            semester_number=data.semester_number,
            status=SessionStatus.DRAFT,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: uuid.UUID) -> ExaminationSession:
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")
        return session

    @staticmethod
    def list_sessions(db: Session) -> List[ExaminationSession]:
        return list(db.execute(select(ExaminationSession).order_by(ExaminationSession.created_at.desc())).scalars().all())

    @staticmethod
    def update_session_status(db: Session, session_id: uuid.UUID, new_status: SessionStatus) -> ExaminationSession:
        session = AcademicService.get_session(db, session_id)
        session.status = new_status
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_session(db: Session, session_id: uuid.UUID, data: ExaminationSessionUpdate) -> ExaminationSession:
        session = AcademicService.get_session(db, session_id)
        if data.name is not None:
            session.name = data.name.strip()
        if data.academic_year is not None:
            session.academic_year = data.academic_year.strip()
        if data.semester_number is not None:
            session.semester_number = data.semester_number
        if data.status is not None:
            session.status = data.status
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: uuid.UUID) -> None:
        session = AcademicService.get_session(db, session_id)
        db.delete(session)
        db.commit()
