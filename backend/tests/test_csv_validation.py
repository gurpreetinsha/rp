import io
import uuid
import pytest
from app.config import settings
from app.core.enums import SessionStatus, BatchStatus, UserRole
from app.core.security import create_access_token


@pytest.fixture
def setup_upload_environment(client, admin_headers):
    """
    Sets up a complete academic testing environment with:
    - Department & Program
    - Course & Open Examination Session (MARKS_ENTRY_OPEN)
    - Assigned Teacher + Teacher Auth Headers
    - 2 Enrolled Students
    """
    # 1. Department & Program
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": f"D_{uuid.uuid4().hex[:6].upper()}", "name": "Computer Science"},
        headers=admin_headers,
    )
    dept_id = dept_res.json()["id"]

    prog_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/programs",
        json={
            "department_id": dept_id,
            "code": f"P_{uuid.uuid4().hex[:6].upper()}",
            "name": "B.Tech Computer Science",
            "total_semesters": 8,
        },
        headers=admin_headers,
    )
    prog_id = prog_res.json()["id"]

    # 2. Course
    course_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={
            "code": f"C_{uuid.uuid4().hex[:6].upper()}",
            "name": "Database Systems",
            "credits": 4.0,
            "pass_percentage": 40.0,
        },
        headers=admin_headers,
    )
    course_id = course_res.json()["id"]

    # 3. Session in MARKS_ENTRY_OPEN status
    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": "Spring 2026 Regular",
            "academic_year": "2026-2027",
            "semester_number": 4,
        },
        headers=admin_headers,
    )
    session_id = session_res.json()["id"]

    client.patch(
        f"{settings.API_V1_PREFIX}/academic/sessions/{session_id}/status",
        json={"status": SessionStatus.MARKS_ENTRY_OPEN.value},
        headers=admin_headers,
    )

    # 4. Teacher + Course Assignment
    teacher_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": f"faculty_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Dr. Database Evaluator",
            "employee_id": f"T_{uuid.uuid4().hex[:6].upper()}",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    teacher_id = teacher_res.json()["id"]
    teacher_user_id = teacher_res.json()["user_id"]

    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/assignments",
        json={"teacher_id": teacher_id, "course_id": course_id, "session_id": session_id},
        headers=admin_headers,
    )

    teacher_token = create_access_token(data={"sub": str(teacher_user_id), "role": UserRole.TEACHER.value})
    t_headers = {"Authorization": f"Bearer {teacher_token}"}

    # 5. Enrolled Students
    stu1_reg = f"REG_{uuid.uuid4().hex[:6].upper()}"
    stu1_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu1_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Alice Resident",
            "registration_number": stu1_reg,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    stu1_id = stu1_res.json()["id"]

    stu2_reg = f"REG_{uuid.uuid4().hex[:6].upper()}"
    stu2_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu2_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Bob Absentee",
            "registration_number": stu2_reg,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    stu2_id = stu2_res.json()["id"]

    # Enroll both students
    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
        json={"student_id": stu1_id, "course_id": course_id, "session_id": session_id},
        headers=admin_headers,
    )
    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
        json={"student_id": stu2_id, "course_id": course_id, "session_id": session_id},
        headers=admin_headers,
    )

    return {
        "session_id": session_id,
        "course_id": course_id,
        "teacher_id": teacher_id,
        "teacher_headers": t_headers,
        "student1_reg": stu1_reg,
        "student2_reg": stu2_reg,
        "prog_id": prog_id,
    }


def test_get_csv_template(client):
    """Test retrieving standard CSV headers and sample structure."""
    res = client.get(f"{settings.API_V1_PREFIX}/imports/template")
    assert res.status_code == 200
    data = res.json()
    assert "columns" in data
    assert "csv_sample" in data
    col_names = [c["name"] for c in data["columns"]]
    assert "registration_number" in col_names
    assert "marks_obtained" in col_names
    assert "is_absent" in col_names


def test_valid_csv_upload_moves_to_pending_approval(client, setup_upload_environment):
    """Test uploading a 100% valid marks CSV stages the batch in PENDING_APPROVAL status."""
    env = setup_upload_environment
    session_id = env["session_id"]
    course_id = env["course_id"]
    t_headers = env["teacher_headers"]
    reg1 = env["student1_reg"]
    reg2 = env["student2_reg"]

    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Alice Resident,85.5,NO,Good performance\n"
        f"{reg2},Bob Absentee,,YES,Excused absence\n"
    )

    form_data = {
        "session_id": str(session_id),
        "course_id": str(course_id),
        "max_marks": "100.0",
    }
    files = {
        "file": ("valid_marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }

    res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data=form_data,
        files=files,
        headers=t_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == BatchStatus.PENDING_APPROVAL.value, data.get("sample_errors")
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert data["error_rows"] == 0
    assert data["max_marks"] == 100.0


def test_csv_with_errors_moves_to_validation_failed(client, setup_upload_environment, admin_headers):
    """Test that any row violation flags the entire batch as VALIDATION_FAILED with line-indexed reports."""
    env = setup_upload_environment
    session_id = env["session_id"]
    course_id = env["course_id"]
    t_headers = env["teacher_headers"]
    reg1 = env["student1_reg"]

    # Create a 3rd student who is NOT enrolled in this course
    not_enrolled_reg = f"REG_NOT_ENROLLED_{uuid.uuid4().hex[:4].upper()}"
    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"unenrolled_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Unenrolled Student",
            "registration_number": not_enrolled_reg,
            "program_id": env["prog_id"],
        },
        headers=admin_headers,
    )

    # Multi-error CSV:
    # Row 2: mark 105 exceeds max_marks 100
    # Row 3: student not enrolled
    # Row 4: nonexistent student
    # Row 5: absent but marks 50 provided
    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Alice,105.0,NO,Exceeds maximum\n"
        f"{not_enrolled_reg},Unenrolled,60.0,NO,Not enrolled in DB course\n"
        "REG_NONEXISTENT_999,Ghost Student,75.0,NO,Fake student\n"
        f"{reg1},Alice Duplicate,50.0,YES,Absent with marks\n"
    )

    form_data = {
        "session_id": str(session_id),
        "course_id": str(course_id),
        "max_marks": "100.0",
    }
    files = {
        "file": ("invalid_marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }

    res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data=form_data,
        files=files,
        headers=t_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == BatchStatus.VALIDATION_FAILED.value
    assert data["error_rows"] > 0
    assert len(data["sample_errors"]) > 0

    batch_id = data["id"]
    # Check row endpoint filtering errors only
    rows_res = client.get(f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/rows?errors_only=true", headers=t_headers)
    assert rows_res.status_code == 200
    rows_data = rows_res.json()
    assert len(rows_data) == data["error_rows"]


def test_duplicate_file_upload_rejected(client, setup_upload_environment):
    """Test that uploading the exact identical file twice is rejected with 409 Conflict."""
    env = setup_upload_environment
    session_id = env["session_id"]
    course_id = env["course_id"]
    t_headers = env["teacher_headers"]
    reg1 = env["student1_reg"]

    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Alice,55.0,NO,First upload\n"
    )

    form_data = {
        "session_id": str(session_id),
        "course_id": str(course_id),
        "max_marks": "100.0",
    }

    # Upload 1
    files1 = {"file": ("dup_check.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res1 = client.post(f"{settings.API_V1_PREFIX}/imports/upload", data=form_data, files=files1, headers=t_headers)
    assert res1.status_code == 201

    # Upload 2 (identical file bytes)
    files2 = {"file": ("dup_check.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res2 = client.post(f"{settings.API_V1_PREFIX}/imports/upload", data=form_data, files=files2, headers=t_headers)
    assert res2.status_code == 409
    assert "identical file" in res2.json()["error"]["message"]


def test_unassigned_teacher_upload_rejected(client, setup_upload_environment, teacher_headers):
    """Test that a teacher NOT assigned to the course cannot upload marks (403 Forbidden)."""
    env = setup_upload_environment
    session_id = env["session_id"]
    course_id = env["course_id"]

    csv_content = "registration_number,student_name,marks_obtained,is_absent,remarks\n"
    form_data = {
        "session_id": str(session_id),
        "course_id": str(course_id),
        "max_marks": "100.0",
    }
    files = {"file": ("marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    # teacher_headers belongs to a generic fixture teacher not assigned to this course
    res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data=form_data,
        files=files,
        headers=teacher_headers,
    )
    assert res.status_code == 403
    assert "not assigned" in res.json()["error"]["message"]
