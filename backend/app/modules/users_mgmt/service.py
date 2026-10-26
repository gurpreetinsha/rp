import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User
from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.users_mgmt.models import Student, Teacher, CourseEnrollment, TeacherCourseAssignment
from app.modules.users_mgmt.schemas import (
    TeacherCreate, TeacherUpdate, TeacherOut,
    StudentCreate, StudentUpdate, StudentOut,
    EnrollmentCreate, EnrollmentBatchCreate, EnrollmentOut,
    AssignmentCreate, AssignmentOut,
)
from app.core.enums import UserRole
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, ConflictException


class UsersManagementService:
    """Business logic for Teacher, Student, Enrollment, and Course Assignment management."""

    # ---------------- Teacher Management ----------------
    @staticmethod
    def create_teacher(db: Session, data: TeacherCreate) -> TeacherOut:
        # Verify department exists
        dept = db.get(Department, data.department_id)
        if not dept:
            raise NotFoundException(f"Department with ID {data.department_id} not found")

        # Verify email uniqueness
        email_normalized = data.email.strip().lower()
        existing_user = db.execute(select(User).where(User.email == email_normalized)).scalar_one_or_none()
        if existing_user:
            raise ConflictException(f"User with email '{data.email}' already exists")

        # Verify employee_id uniqueness
        emp_id_normalized = data.employee_id.strip().upper()
        existing_teacher = db.execute(select(Teacher).where(Teacher.employee_id == emp_id_normalized)).scalar_one_or_none()
        if existing_teacher:
            raise ConflictException(f"Teacher with Employee ID '{data.employee_id}' already exists")

        # Transactionally create User + Teacher
        user = User(
            email=email_normalized,
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(user)
        db.flush()

        teacher = Teacher(
            user_id=user.id,
            employee_id=emp_id_normalized,
            department_id=data.department_id,
            designation=data.designation.strip(),
            is_active=True,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        db.refresh(user)

        return TeacherOut(
            id=teacher.id,
            user_id=user.id,
            employee_id=teacher.employee_id,
            department_id=teacher.department_id,
            designation=teacher.designation,
            is_active=teacher.is_active,
            full_name=user.full_name,
            email=user.email,
            created_at=teacher.created_at,
            updated_at=teacher.updated_at,
        )

    @staticmethod
    def get_teacher(db: Session, teacher_id: uuid.UUID) -> TeacherOut:
        teacher = db.execute(
            select(Teacher).options(joinedload(Teacher.user)).where(Teacher.id == teacher_id)
        ).scalar_one_or_none()
        if not teacher:
            raise NotFoundException(f"Teacher with ID {teacher_id} not found")

        return TeacherOut(
            id=teacher.id,
            user_id=teacher.user_id,
            employee_id=teacher.employee_id,
            department_id=teacher.department_id,
            designation=teacher.designation,
            is_active=teacher.is_active,
            full_name=teacher.user.full_name,
            email=teacher.user.email,
            created_at=teacher.created_at,
            updated_at=teacher.updated_at,
        )

    @staticmethod
    def get_teacher_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[Teacher]:
        return db.execute(
            select(Teacher).where(Teacher.user_id == user_id)
        ).scalar_one_or_none()

    @staticmethod
    def list_teachers(db: Session, department_id: Optional[uuid.UUID] = None, active_only: bool = True) -> List[TeacherOut]:
        query = select(Teacher).options(joinedload(Teacher.user))
        if department_id:
            query = query.where(Teacher.department_id == department_id)
        if active_only:
            query = query.where(Teacher.is_active == True)

        teachers = db.execute(query.order_by(Teacher.created_at.desc())).scalars().all()
        return [
            TeacherOut(
                id=t.id,
                user_id=t.user_id,
                employee_id=t.employee_id,
                department_id=t.department_id,
                designation=t.designation,
                is_active=t.is_active,
                full_name=t.user.full_name,
                email=t.user.email,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in teachers
        ]

    # ---------------- Student Management ----------------
    @staticmethod
    def create_student(db: Session, data: StudentCreate) -> StudentOut:
        # Verify program exists
        prog = db.get(Program, data.program_id)
        if not prog:
            raise NotFoundException(f"Program with ID {data.program_id} not found")

        # Verify email uniqueness
        email_normalized = data.email.strip().lower()
        existing_user = db.execute(select(User).where(User.email == email_normalized)).scalar_one_or_none()
        if existing_user:
            raise ConflictException(f"User with email '{data.email}' already exists")

        # Verify registration_number uniqueness
        reg_no_normalized = data.registration_number.strip().upper()
        existing_student = db.execute(select(Student).where(Student.registration_number == reg_no_normalized)).scalar_one_or_none()
        if existing_student:
            raise ConflictException(f"Student with Registration Number '{data.registration_number}' already exists")

        # Transactionally create User + Student
        user = User(
            email=email_normalized,
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            registration_number=reg_no_normalized,
            roll_number=data.roll_number.strip() if data.roll_number else None,
            program_id=data.program_id,
            current_semester=data.current_semester,
            is_active=True,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        db.refresh(user)

        return StudentOut(
            id=student.id,
            user_id=user.id,
            registration_number=student.registration_number,
            roll_number=student.roll_number,
            program_id=student.program_id,
            current_semester=student.current_semester,
            is_active=student.is_active,
            full_name=user.full_name,
            email=user.email,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    @staticmethod
    def get_student(db: Session, student_id: uuid.UUID) -> StudentOut:
        student = db.execute(
            select(Student).options(joinedload(Student.user)).where(Student.id == student_id)
        ).scalar_one_or_none()
        if not student:
            raise NotFoundException(f"Student with ID {student_id} not found")

        return StudentOut(
            id=student.id,
            user_id=student.user_id,
            registration_number=student.registration_number,
            roll_number=student.roll_number,
            program_id=student.program_id,
            current_semester=student.current_semester,
            is_active=student.is_active,
            full_name=student.user.full_name,
            email=student.user.email,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    @staticmethod
    def get_student_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[Student]:
        return db.execute(
            select(Student).where(Student.user_id == user_id)
        ).scalar_one_or_none()

    @staticmethod
    def list_students(
        db: Session,
        program_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
        active_only: bool = True,
    ) -> List[StudentOut]:
        query = select(Student).options(joinedload(Student.user))
        if program_id:
            query = query.where(Student.program_id == program_id)
        if semester:
            query = query.where(Student.current_semester == semester)
        if active_only:
            query = query.where(Student.is_active == True)

        students = db.execute(query.order_by(Student.registration_number)).scalars().all()
        return [
            StudentOut(
                id=s.id,
                user_id=s.user_id,
                registration_number=s.registration_number,
                roll_number=s.roll_number,
                program_id=s.program_id,
                current_semester=s.current_semester,
                is_active=s.is_active,
                full_name=s.user.full_name,
                email=s.user.email,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in students
        ]

    # ---------------- Course Enrollment Management ----------------
    @staticmethod
    def enroll_student(db: Session, data: EnrollmentCreate) -> EnrollmentOut:
        # Validate student, course, session exist
        student = db.execute(
            select(Student).options(joinedload(Student.user)).where(Student.id == data.student_id)
        ).scalar_one_or_none()
        if not student:
            raise NotFoundException(f"Student with ID {data.student_id} not found")

        course = db.get(Course, data.course_id)
        if not course:
            raise NotFoundException(f"Course with ID {data.course_id} not found")

        session = db.get(ExaminationSession, data.session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {data.session_id} not found")

        # Check existing enrollment
        existing = db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.student_id == data.student_id,
                CourseEnrollment.course_id == data.course_id,
                CourseEnrollment.session_id == data.session_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Student '{student.registration_number}' is already enrolled in this course for this session")

        enrollment = CourseEnrollment(
            student_id=data.student_id,
            course_id=data.course_id,
            session_id=data.session_id,
            is_active=True,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        return EnrollmentOut(
            id=enrollment.id,
            student_id=student.id,
            course_id=course.id,
            session_id=session.id,
            is_active=enrollment.is_active,
            registration_number=student.registration_number,
            student_name=student.user.full_name,
            course_code=course.code,
            course_name=course.name,
            created_at=enrollment.created_at,
        )

    @staticmethod
    def list_enrollments(
        db: Session,
        session_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        student_id: Optional[uuid.UUID] = None,
    ) -> List[EnrollmentOut]:
        query = select(CourseEnrollment).options(
            joinedload(CourseEnrollment.student).joinedload(Student.user),
            joinedload(CourseEnrollment.course),
        )
        if session_id:
            query = query.where(CourseEnrollment.session_id == session_id)
        if course_id:
            query = query.where(CourseEnrollment.course_id == course_id)
        if student_id:
            query = query.where(CourseEnrollment.student_id == student_id)

        enrollments = db.execute(query).scalars().all()
        return [
            EnrollmentOut(
                id=e.id,
                student_id=e.student_id,
                course_id=e.course_id,
                session_id=e.session_id,
                is_active=e.is_active,
                registration_number=e.student.registration_number,
                student_name=e.student.user.full_name,
                course_code=e.course.code,
                course_name=e.course.name,
                created_at=e.created_at,
            )
            for e in enrollments
        ]

    # ---------------- Teacher Assignment Management ----------------
    @staticmethod
    def assign_teacher(db: Session, data: AssignmentCreate) -> AssignmentOut:
        # Validate teacher, course, session exist
        teacher = db.execute(
            select(Teacher).options(joinedload(Teacher.user)).where(Teacher.id == data.teacher_id)
        ).scalar_one_or_none()
        if not teacher:
            raise NotFoundException(f"Teacher with ID {data.teacher_id} not found")

        course = db.get(Course, data.course_id)
        if not course:
            raise NotFoundException(f"Course with ID {data.course_id} not found")

        session = db.get(ExaminationSession, data.session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {data.session_id} not found")

        # Check existing assignment
        existing = db.execute(
            select(TeacherCourseAssignment).where(
                TeacherCourseAssignment.teacher_id == data.teacher_id,
                TeacherCourseAssignment.course_id == data.course_id,
                TeacherCourseAssignment.session_id == data.session_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Teacher '{teacher.employee_id}' is already assigned to this course for this session")

        assignment = TeacherCourseAssignment(
            teacher_id=data.teacher_id,
            course_id=data.course_id,
            session_id=data.session_id,
            is_active=True,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return AssignmentOut(
            id=assignment.id,
            teacher_id=teacher.id,
            course_id=course.id,
            session_id=session.id,
            is_active=assignment.is_active,
            teacher_name=teacher.user.full_name,
            employee_id=teacher.employee_id,
            course_code=course.code,
            course_name=course.name,
            session_name=session.name,
            created_at=assignment.created_at,
        )

    @staticmethod
    def list_assignments(
        db: Session,
        teacher_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
    ) -> List[AssignmentOut]:
        query = select(TeacherCourseAssignment).options(
            joinedload(TeacherCourseAssignment.teacher).joinedload(Teacher.user),
            joinedload(TeacherCourseAssignment.course),
            joinedload(TeacherCourseAssignment.session),
        )
        if teacher_id:
            query = query.where(TeacherCourseAssignment.teacher_id == teacher_id)
        if session_id:
            query = query.where(TeacherCourseAssignment.session_id == session_id)
        if course_id:
            query = query.where(TeacherCourseAssignment.course_id == course_id)

        assignments = db.execute(query).scalars().all()
        return [
            AssignmentOut(
                id=a.id,
                teacher_id=a.teacher_id,
                course_id=a.course_id,
                session_id=a.session_id,
                is_active=a.is_active,
                teacher_name=a.teacher.user.full_name,
                employee_id=a.teacher.employee_id,
                course_code=a.course.code,
                course_name=a.course.name,
                session_name=a.session.name,
                created_at=a.created_at,
            )
            for a in assignments
        ]
