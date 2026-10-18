import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.auth.models import User
from app.modules.users_mgmt.models import Student, CourseEnrollment
from app.modules.marks.models import OfficialMark
from app.modules.imports.models import MarkImportBatch
from app.modules.results.models import CalculatedResult
from app.core.enums import UserRole, SessionStatus, BatchStatus, ResultStatus


def test_create_and_get_department(client):
    """Test department creation and retrieval."""
    payload = {"code": "CSE", "name": "Computer Science and Engineering"}
    res = client.post(f"{settings.API_V1_PREFIX}/academic/departments", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "CSE"
    assert data["name"] == "Computer Science and Engineering"
    assert "id" in data

    dept_id = data["id"]
    get_res = client.get(f"{settings.API_V1_PREFIX}/academic/departments/{dept_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == dept_id


def test_duplicate_department_code_conflict(client):
    """Test that creating a department with an existing code returns 409 Conflict."""
    payload = {"code": "ECE", "name": "Electronics & Communication"}
    res1 = client.post(f"{settings.API_V1_PREFIX}/academic/departments", json=payload)
    assert res1.status_code == 201

    res2 = client.post(f"{settings.API_V1_PREFIX}/academic/departments", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


def test_create_program_under_department(client):
    """Test creating an academic program under an existing department."""
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": "MECH", "name": "Mechanical Engineering"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    prog_payload = {
        "department_id": dept_id,
        "code": "BTECH_MECH",
        "name": "B.Tech in Mechanical Engineering",
        "total_semesters": 8,
    }
    prog_res = client.post(f"{settings.API_V1_PREFIX}/academic/programs", json=prog_payload)
    assert prog_res.status_code == 201
    prog_data = prog_res.json()
    assert prog_data["code"] == "BTECH_MECH"
    assert prog_data["department_id"] == dept_id


def test_program_with_invalid_department_returns_404(client):
    """Test program creation with a non-existent department returns 404."""
    fake_dept_id = str(uuid.uuid4())
    prog_payload = {
        "department_id": fake_dept_id,
        "code": "INVALID_PROG",
        "name": "Invalid Program",
        "total_semesters": 4,
    }
    res = client.post(f"{settings.API_V1_PREFIX}/academic/programs", json=prog_payload)
    assert res.status_code == 404


def test_create_and_update_course(client):
    """Test course creation, default values, and patch updates."""
    payload = {
        "code": "CS101",
        "name": "Introduction to Programming",
        "credits": 4.0,
        "pass_percentage": 40.0,
    }
    res = client.post(f"{settings.API_V1_PREFIX}/academic/courses", json=payload)
    assert res.status_code == 201
    course_data = res.json()
    assert course_data["code"] == "CS101"
    assert course_data["pass_percentage"] == 40.0
    course_id = course_data["id"]

    # Patch update course name and pass percentage
    patch_res = client.patch(
        f"{settings.API_V1_PREFIX}/academic/courses/{course_id}",
        json={"pass_percentage": 50.0, "name": "Intro to Programming in Python"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["pass_percentage"] == 50.0
    assert patch_res.json()["name"] == "Intro to Programming in Python"


def test_create_and_transition_examination_session(client):
    """Test examination session creation in DRAFT and lifecycle status transition."""
    session_payload = {
        "name": "Fall 2026 Regular Exams",
        "academic_year": "2026-2027",
        "semester_number": 3,
    }
    res = client.post(f"{settings.API_V1_PREFIX}/academic/sessions", json=session_payload)
    assert res.status_code == 201
    session_data = res.json()
    assert session_data["status"] == SessionStatus.DRAFT.value
    session_id = session_data["id"]

    # Transition to MARKS_ENTRY_OPEN
    status_res = client.patch(
        f"{settings.API_V1_PREFIX}/academic/sessions/{session_id}/status",
        json={"status": SessionStatus.MARKS_ENTRY_OPEN.value},
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == SessionStatus.MARKS_ENTRY_OPEN.value


def test_database_enrollment_unique_constraint(db_session):
    """Test that the database enforces UNIQUE(student_id, course_id, session_id)."""
    # Create required base records
    user = User(
        email="student_test@example.com",
        hashed_password="hashed_dummy_pw",
        full_name="Test Student",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    db_session.flush()

    dept = Department(code="PHYS", name="Physics")
    db_session.add(dept)
    db_session.flush()

    prog = Program(department_id=dept.id, code="BSC_PHYS", name="B.Sc Physics", total_semesters=6)
    db_session.add(prog)
    db_session.flush()

    student = Student(user_id=user.id, registration_number="REG_PHYS_001", program_id=prog.id)
    course = Course(code="PHYS101", name="Mechanics")
    session = ExaminationSession(name="Session 1", academic_year="2026", semester_number=1)
    db_session.add_all([student, course, session])
    db_session.flush()

    # First enrollment succeeds
    enrollment1 = CourseEnrollment(student_id=student.id, course_id=course.id, session_id=session.id)
    db_session.add(enrollment1)
    db_session.flush()

    # Duplicate enrollment violates unique constraint
    enrollment2 = CourseEnrollment(student_id=student.id, course_id=course.id, session_id=session.id)
    db_session.add(enrollment2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_database_official_mark_unique_constraint(db_session):
    """Test that official_marks enforces UNIQUE(session_id, course_id, student_id)."""
    user_s = User(email="s2@example.com", hashed_password="pw", full_name="S2", role=UserRole.STUDENT)
    user_t = User(email="t1@example.com", hashed_password="pw", full_name="T1", role=UserRole.TEACHER)
    db_session.add_all([user_s, user_t])
    db_session.flush()

    dept = Department(code="MATH", name="Mathematics")
    db_session.add(dept)
    db_session.flush()

    prog = Program(department_id=dept.id, code="BSC_MATH", name="B.Sc Math", total_semesters=6)
    from app.modules.users_mgmt.models import Teacher
    teacher = Teacher(user_id=user_t.id, employee_id="T_MATH_01", department_id=dept.id)
    db_session.add_all([prog, teacher])
    db_session.flush()

    student = Student(user_id=user_s.id, registration_number="REG_MATH_002", program_id=prog.id)
    course = Course(code="MATH101", name="Calculus I")
    session = ExaminationSession(name="Math Exams", academic_year="2026", semester_number=1)
    db_session.add_all([student, course, session])
    db_session.flush()

    batch = MarkImportBatch(
        session_id=session.id,
        course_id=course.id,
        uploaded_by_teacher_id=teacher.id,
        max_marks=100.0,
        file_name="marks.csv",
        file_hash="dummy_hash_123",
        status=BatchStatus.IMPORTED,
    )
    db_session.add(batch)
    db_session.flush()

    # Add first official mark
    mark1 = OfficialMark(
        session_id=session.id,
        course_id=course.id,
        student_id=student.id,
        batch_id=batch.id,
        marks_obtained=85.0,
        max_marks=100.0,
    )
    db_session.add(mark1)
    db_session.flush()

    # Attempting to insert duplicate official mark for same student in same course and session
    mark2 = OfficialMark(
        session_id=session.id,
        course_id=course.id,
        student_id=student.id,
        batch_id=batch.id,
        marks_obtained=90.0,
        max_marks=100.0,
    )
    db_session.add(mark2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
