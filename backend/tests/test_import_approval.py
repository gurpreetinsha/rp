import io
import uuid
import pytest
from app.config import settings
from app.core.enums import SessionStatus, BatchStatus, UserRole
from app.core.security import create_access_token


@pytest.fixture
def setup_pending_batch_env(client, admin_headers):
    """Sets up an environment with an open session, course, teacher, 2 enrolled students, and a PENDING_APPROVAL batch."""
    # 1. Department & Program
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": f"D_{uuid.uuid4().hex[:6].upper()}", "name": "Computer Engineering"},
        headers=admin_headers,
    )
    dept_id = dept_res.json()["id"]

    prog_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/programs",
        json={
            "department_id": dept_id,
            "code": f"P_{uuid.uuid4().hex[:6].upper()}",
            "name": "B.Tech Computer Engineering",
            "total_semesters": 8,
        },
        headers=admin_headers,
    )
    prog_id = prog_res.json()["id"]

    # 2. Course & Open Session
    course_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={
            "code": f"C_{uuid.uuid4().hex[:6].upper()}",
            "name": "Operating Systems",
            "credits": 4.0,
            "pass_percentage": 40.0,
        },
        headers=admin_headers,
    )
    course_id = course_res.json()["id"]

    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": "Fall 2026 Regular OS Exam",
            "academic_year": "2026-2027",
            "semester_number": 5,
        },
        headers=admin_headers,
    )
    session_id = session_res.json()["id"]

    client.patch(
        f"{settings.API_V1_PREFIX}/academic/sessions/{session_id}/status",
        json={"status": SessionStatus.MARKS_ENTRY_OPEN.value},
        headers=admin_headers,
    )

    # 3. Teacher + Assignment
    teacher_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": f"faculty_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Prof. OS Evaluator",
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

    # 4. Two Enrolled Students
    reg1 = f"REG_{uuid.uuid4().hex[:6].upper()}"
    stu1_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu1_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Student Passed",
            "registration_number": reg1,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    stu1_id = stu1_res.json()["id"]

    reg2 = f"REG_{uuid.uuid4().hex[:6].upper()}"
    stu2_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu2_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Student Absent",
            "registration_number": reg2,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    stu2_id = stu2_res.json()["id"]

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

    # 5. Upload Valid Marks File -> PENDING_APPROVAL
    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Student Passed,92.5,NO,Top score\n"
        f"{reg2},Student Absent,,YES,Medical leave\n"
    )
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(course_id), "max_marks": "100.0"},
        files={"file": ("os_marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=t_headers,
    )
    assert upload_res.status_code == 201
    batch_data = upload_res.json()
    assert batch_data["status"] == BatchStatus.PENDING_APPROVAL.value

    return {
        "session_id": session_id,
        "course_id": course_id,
        "batch_id": batch_data["id"],
        "student1_reg": reg1,
        "student2_reg": reg2,
        "teacher_headers": t_headers,
    }


def test_admin_approve_batch_transfers_to_official_marks(client, admin_headers, setup_pending_batch_env):
    """Test that Admin approving a PENDING_APPROVAL batch transitions it to IMPORTED and populates official_marks."""
    env = setup_pending_batch_env
    batch_id = env["batch_id"]
    session_id = env["session_id"]
    course_id = env["course_id"]
    reg1 = env["student1_reg"]
    reg2 = env["student2_reg"]

    # Approve batch
    approve_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve",
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    batch_out = approve_res.json()
    assert batch_out["status"] == BatchStatus.IMPORTED.value
    assert batch_out["reviewed_by_admin_id"] is not None
    assert batch_out["reviewed_at"] is not None

    # Query official marks
    marks_res = client.get(
        f"{settings.API_V1_PREFIX}/marks/official?session_id={session_id}&course_id={course_id}",
        headers=admin_headers,
    )
    assert marks_res.status_code == 200
    marks = marks_res.json()
    assert len(marks) == 2

    # Map by registration number
    marks_map = {m["registration_number"]: m for m in marks}
    assert marks_map[reg1]["marks_obtained"] == 92.5
    assert marks_map[reg1]["is_absent"] is False
    assert marks_map[reg1]["percentage"] == 92.5

    assert marks_map[reg2]["marks_obtained"] == 0.0
    assert marks_map[reg2]["is_absent"] is True
    assert marks_map[reg2]["percentage"] == 0.0


def test_admin_reject_batch(client, admin_headers, setup_pending_batch_env):
    """Test that Admin rejecting a batch sets REJECTED status and reason without creating official marks."""
    env = setup_pending_batch_env
    batch_id = env["batch_id"]
    session_id = env["session_id"]
    course_id = env["course_id"]

    reject_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/reject",
        json={"reason": "Incorrect evaluation rubrics applied. Please re-check."},
        headers=admin_headers,
    )
    assert reject_res.status_code == 200
    batch_out = reject_res.json()
    assert batch_out["status"] == BatchStatus.REJECTED.value
    assert batch_out["rejection_reason"] == "Incorrect evaluation rubrics applied. Please re-check."

    # Official marks must remain empty
    marks_res = client.get(
        f"{settings.API_V1_PREFIX}/marks/official?session_id={session_id}&course_id={course_id}",
        headers=admin_headers,
    )
    assert marks_res.status_code == 200
    assert len(marks_res.json()) == 0


def test_duplicate_approval_rejected(client, admin_headers, setup_pending_batch_env):
    """Test that repeated approval requests return 409 Conflict without duplicating data."""
    env = setup_pending_batch_env
    batch_id = env["batch_id"]

    # First approval succeeds
    res1 = client.post(f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve", headers=admin_headers)
    assert res1.status_code == 200

    # Second approval request returns 409 Conflict
    res2 = client.post(f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve", headers=admin_headers)
    assert res2.status_code == 409
    assert "already been approved" in res2.json()["error"]["message"]


def test_teacher_cannot_approve_or_reject_batch(client, setup_pending_batch_env):
    """Test that faculty members cannot approve or reject their own batches (403 Forbidden)."""
    env = setup_pending_batch_env
    batch_id = env["batch_id"]
    t_headers = env["teacher_headers"]

    approve_res = client.post(f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve", headers=t_headers)
    assert approve_res.status_code == 403

    reject_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/reject",
        json={"reason": "Self rejection"},
        headers=t_headers,
    )
    assert reject_res.status_code == 403


def test_student_cannot_view_official_marks(client, student_headers, setup_pending_batch_env):
    """Test that students cannot directly query official marks endpoint (403 Forbidden)."""
    env = setup_pending_batch_env
    session_id = env["session_id"]
    course_id = env["course_id"]

    res = client.get(
        f"{settings.API_V1_PREFIX}/marks/official?session_id={session_id}&course_id={course_id}",
        headers=student_headers,
    )
    assert res.status_code == 403
