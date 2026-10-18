import uuid
import pytest
from app.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token


@pytest.fixture
def test_setup_dept_and_prog(client, admin_headers):
    """Helper fixture providing an academic department, program, course, and session."""
    # Create Department
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": f"DEPT_{uuid.uuid4().hex[:6].upper()}", "name": "Department of Science"},
        headers=admin_headers,
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    # Create Program
    prog_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/programs",
        json={
            "department_id": dept_id,
            "code": f"PROG_{uuid.uuid4().hex[:6].upper()}",
            "name": "Bachelor of Science",
            "total_semesters": 6,
        },
        headers=admin_headers,
    )
    assert prog_res.status_code == 201
    prog_id = prog_res.json()["id"]

    # Create Course
    course_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={
            "code": f"CRS_{uuid.uuid4().hex[:6].upper()}",
            "name": "General Science 101",
            "credits": 3.0,
            "pass_percentage": 40.0,
        },
        headers=admin_headers,
    )
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # Create Session
    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": "Semester Exams 2026",
            "academic_year": "2026-2027",
            "semester_number": 1,
        },
        headers=admin_headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    return {
        "dept_id": dept_id,
        "prog_id": prog_id,
        "course_id": course_id,
        "session_id": session_id,
    }


def test_create_teacher_success(client, admin_headers, test_setup_dept_and_prog):
    """Test admin registering a faculty member."""
    dept_id = test_setup_dept_and_prog["dept_id"]
    emp_id = f"EMP_{uuid.uuid4().hex[:6].upper()}"
    email = f"prof_{uuid.uuid4().hex[:6]}@institution.edu"

    payload = {
        "email": email,
        "password": "FacultyStrongPassword123!",
        "full_name": "Prof. Albus Dumbledore",
        "employee_id": emp_id,
        "department_id": dept_id,
        "designation": "Head of Department",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/teachers", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["employee_id"] == emp_id
    assert data["email"] == email.lower()
    assert data["full_name"] == "Prof. Albus Dumbledore"
    assert "user_id" in data
    assert "id" in data


def test_create_teacher_duplicate_employee_id(client, admin_headers, test_setup_dept_and_prog):
    """Test creating teacher with duplicate employee_id returns 409 Conflict."""
    dept_id = test_setup_dept_and_prog["dept_id"]
    emp_id = "EMP_DUPLICATE_001"

    payload1 = {
        "email": "teacher1@institution.edu",
        "password": "Password123!",
        "full_name": "Teacher One",
        "employee_id": emp_id,
        "department_id": dept_id,
    }
    res1 = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/teachers", json=payload1, headers=admin_headers)
    assert res1.status_code == 201

    payload2 = {
        "email": "teacher2@institution.edu",
        "password": "Password123!",
        "full_name": "Teacher Two",
        "employee_id": emp_id,
        "department_id": dept_id,
    }
    res2 = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/teachers", json=payload2, headers=admin_headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


def test_create_student_success(client, admin_headers, test_setup_dept_and_prog):
    """Test admin registering a student."""
    prog_id = test_setup_dept_and_prog["prog_id"]
    reg_no = f"REG_{uuid.uuid4().hex[:6].upper()}"
    email = f"student_{uuid.uuid4().hex[:6]}@institution.edu"

    payload = {
        "email": email,
        "password": "StudentPassword123!",
        "full_name": "Harry Potter",
        "registration_number": reg_no,
        "roll_number": "HP-01",
        "program_id": prog_id,
        "current_semester": 1,
    }
    res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/students", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["registration_number"] == reg_no
    assert data["email"] == email.lower()
    assert data["roll_number"] == "HP-01"


def test_create_student_duplicate_registration_number(client, admin_headers, test_setup_dept_and_prog):
    """Test creating student with duplicate registration_number returns 409 Conflict."""
    prog_id = test_setup_dept_and_prog["prog_id"]
    reg_no = "REG_DUPLICATE_001"

    payload1 = {
        "email": "s1@institution.edu",
        "password": "Password123!",
        "full_name": "Student A",
        "registration_number": reg_no,
        "program_id": prog_id,
    }
    res1 = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/students", json=payload1, headers=admin_headers)
    assert res1.status_code == 201

    payload2 = {
        "email": "s2@institution.edu",
        "password": "Password123!",
        "full_name": "Student B",
        "registration_number": reg_no,
        "program_id": prog_id,
    }
    res2 = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/students", json=payload2, headers=admin_headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


def test_enroll_student_in_course(client, admin_headers, test_setup_dept_and_prog):
    """Test enrolling a student in a course for an examination session."""
    prog_id = test_setup_dept_and_prog["prog_id"]
    course_id = test_setup_dept_and_prog["course_id"]
    session_id = test_setup_dept_and_prog["session_id"]

    # Create student
    stu_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Enrolled Student",
            "registration_number": f"REG_{uuid.uuid4().hex[:6].upper()}",
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    assert stu_res.status_code == 201
    student_id = stu_res.json()["id"]

    enroll_payload = {
        "student_id": student_id,
        "course_id": course_id,
        "session_id": session_id,
    }
    enroll_res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/enrollments", json=enroll_payload, headers=admin_headers)
    assert enroll_res.status_code == 201
    data = enroll_res.json()
    assert data["student_id"] == student_id
    assert data["course_id"] == course_id
    assert data["session_id"] == session_id

    # Duplicate enrollment check
    duplicate_res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/enrollments", json=enroll_payload, headers=admin_headers)
    assert duplicate_res.status_code == 409
    assert "already enrolled" in duplicate_res.json()["error"]["message"]


def test_assign_teacher_to_course_and_query_my_assignments(client, admin_headers, test_setup_dept_and_prog):
    """Test assigning teacher to course and teacher retrieving their assigned courses."""
    dept_id = test_setup_dept_and_prog["dept_id"]
    course_id = test_setup_dept_and_prog["course_id"]
    session_id = test_setup_dept_and_prog["session_id"]

    teacher_email = f"faculty_{uuid.uuid4().hex[:6]}@institution.edu"
    teacher_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": teacher_email,
            "password": "Password123!",
            "full_name": "Prof. Assigned",
            "employee_id": f"EMP_{uuid.uuid4().hex[:6].upper()}",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]
    teacher_user_id = teacher_res.json()["user_id"]

    assign_payload = {
        "teacher_id": teacher_id,
        "course_id": course_id,
        "session_id": session_id,
    }
    assign_res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/assignments", json=assign_payload, headers=admin_headers)
    assert assign_res.status_code == 201
    assert assign_res.json()["teacher_id"] == teacher_id

    # Duplicate assignment check
    dup_assign_res = client.post(f"{settings.API_V1_PREFIX}/users-mgmt/assignments", json=assign_payload, headers=admin_headers)
    assert dup_assign_res.status_code == 409

    # Generate token for this specific teacher
    teacher_token = create_access_token(data={"sub": str(teacher_user_id), "role": UserRole.TEACHER.value})
    t_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Query assigned courses as teacher
    my_assign_res = client.get(f"{settings.API_V1_PREFIX}/users-mgmt/teachers/me/assignments", headers=t_headers)
    assert my_assign_res.status_code == 200
    my_assignments = my_assign_res.json()
    assert len(my_assignments) == 1
    assert my_assignments[0]["course_id"] == course_id


def test_student_get_my_profile_and_denied_admin_routes(client, admin_headers, test_setup_dept_and_prog):
    """Test student retrieving own profile, and verifying student cannot list all students."""
    prog_id = test_setup_dept_and_prog["prog_id"]
    stu_email = f"stu_{uuid.uuid4().hex[:6]}@institution.edu"
    stu_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": stu_email,
            "password": "Password123!",
            "full_name": "Hermione Granger",
            "registration_number": f"REG_{uuid.uuid4().hex[:6].upper()}",
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    assert stu_res.status_code == 201
    student_user_id = stu_res.json()["user_id"]

    # Student token
    student_token = create_access_token(data={"sub": str(student_user_id), "role": UserRole.STUDENT.value})
    s_headers = {"Authorization": f"Bearer {student_token}"}

    # Student retrieves own profile
    me_res = client.get(f"{settings.API_V1_PREFIX}/users-mgmt/students/me", headers=s_headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Hermione Granger"

    # Student attempts to list all students -> 403 Forbidden
    forbidden_res = client.get(f"{settings.API_V1_PREFIX}/users-mgmt/students", headers=s_headers)
    assert forbidden_res.status_code == 403
