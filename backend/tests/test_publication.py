import io
import uuid
import pytest
from app.config import settings
from app.core.enums import SessionStatus, ResultStatus, UserRole
from app.core.security import create_access_token


@pytest.fixture
def setup_published_env(client, admin_headers):
    """Sets up a fully calculated examination session with 2 courses and 2 students."""
    # 1. Department & Program
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": f"D_{uuid.uuid4().hex[:6].upper()}", "name": "Information Technology"},
        headers=admin_headers,
    )
    dept_id = dept_res.json()["id"]

    prog_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/programs",
        json={
            "department_id": dept_id,
            "code": f"P_{uuid.uuid4().hex[:6].upper()}",
            "name": "B.Tech Information Technology",
            "total_semesters": 8,
        },
        headers=admin_headers,
    )
    prog_id = prog_res.json()["id"]

    # 2. Examination Session
    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": f"Session_{uuid.uuid4().hex[:6]}",
            "academic_year": "2026-2027",
            "semester_number": 6,
        },
        headers=admin_headers,
    )
    session_id = session_res.json()["id"]

    client.patch(
        f"{settings.API_V1_PREFIX}/academic/sessions/{session_id}/status",
        json={"status": SessionStatus.MARKS_ENTRY_OPEN.value},
        headers=admin_headers,
    )

    # 3. Two Courses
    c1_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={"code": f"IT_{uuid.uuid4().hex[:6].upper()}", "name": "Cloud Computing", "credits": 4.0, "pass_percentage": 40.0},
        headers=admin_headers,
    )
    c1_id = c1_res.json()["id"]

    c2_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={"code": f"IT_{uuid.uuid4().hex[:6].upper()}", "name": "Cyber Security", "credits": 3.0, "pass_percentage": 40.0},
        headers=admin_headers,
    )
    c2_id = c2_res.json()["id"]

    # 4. Teacher + Course Assignments
    t_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": f"prof_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Prof. Linus Torvalds",
            "employee_id": f"T_{uuid.uuid4().hex[:6].upper()}",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    t_id = t_res.json()["id"]
    t_user_id = t_res.json()["user_id"]

    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/assignments",
        json={"teacher_id": t_id, "course_id": c1_id, "session_id": session_id},
        headers=admin_headers,
    )
    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/assignments",
        json={"teacher_id": t_id, "course_id": c2_id, "session_id": session_id},
        headers=admin_headers,
    )

    teacher_token = create_access_token(data={"sub": str(t_user_id), "role": UserRole.TEACHER.value})
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # 5. Two Students
    reg1 = f"STU_{uuid.uuid4().hex[:6].upper()}"
    reg2 = f"STU_{uuid.uuid4().hex[:6].upper()}"

    s1_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu1_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Alice Pass",
            "registration_number": reg1,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    s1_id = s1_res.json()["id"]
    s1_user_id = s1_res.json()["user_id"]

    s2_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu2_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Bob Withheld",
            "registration_number": reg2,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    s2_id = s2_res.json()["id"]
    s2_user_id = s2_res.json()["user_id"]

    # Enrollments
    for sid in [s1_id, s2_id]:
        client.post(
            f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
            json={"student_id": sid, "course_id": c1_id, "session_id": session_id},
            headers=admin_headers,
        )
        client.post(
            f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
            json={"student_id": sid, "course_id": c2_id, "session_id": session_id},
            headers=admin_headers,
        )

    # 6. Upload & Approve Marks for both courses
    csv1 = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Alice Pass,88.0,NO,\n"
        f"{reg2},Bob Withheld,72.0,NO,\n"
    )
    up1 = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(c1_id), "max_marks": "100.0"},
        files={"file": ("c1.csv", io.BytesIO(csv1.encode("utf-8")), "text/csv")},
        headers=teacher_headers,
    )
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{up1.json()['id']}/approve",
        headers=admin_headers,
    )

    csv2 = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg1},Alice Pass,92.0,NO,\n"
        f"{reg2},Bob Withheld,68.0,NO,\n"
    )
    up2 = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(c2_id), "max_marks": "100.0"},
        files={"file": ("c2.csv", io.BytesIO(csv2.encode("utf-8")), "text/csv")},
        headers=teacher_headers,
    )
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{up2.json()['id']}/approve",
        headers=admin_headers,
    )

    # 7. Calculate Results -> CALCULATED
    client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        headers=admin_headers,
    )

    s1_token = create_access_token(data={"sub": str(s1_user_id), "role": UserRole.STUDENT.value})
    s1_headers = {"Authorization": f"Bearer {s1_token}"}

    s2_token = create_access_token(data={"sub": str(s2_user_id), "role": UserRole.STUDENT.value})
    s2_headers = {"Authorization": f"Bearer {s2_token}"}

    return {
        "session_id": session_id,
        "s1_id": s1_id,
        "s2_id": s2_id,
        "s1_headers": s1_headers,
        "s2_headers": s2_headers,
        "teacher_headers": teacher_headers,
        "reg1": reg1,
        "reg2": reg2,
    }


def test_publish_role_enforcement(client, admin_headers, setup_published_env):
    """Teachers and students cannot publish examination results."""
    env = setup_published_env
    session_id = env["session_id"]

    t_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/publish",
        headers=env["teacher_headers"],
    )
    assert t_res.status_code == 403

    s_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/publish",
        headers=env["s1_headers"],
    )
    assert s_res.status_code == 403


def test_student_cannot_view_results_before_publication(client, setup_published_env):
    """Students cannot access any results while the session is still in CALCULATED status."""
    env = setup_published_env
    session_id = env["session_id"]

    # Student 1 tries to list their results -> empty list
    my_res = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=env["s1_headers"],
    )
    assert my_res.status_code == 200
    assert my_res.json() == []

    # Student 1 tries specific session endpoint -> 404
    my_sess_res = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results/sessions/{session_id}",
        headers=env["s1_headers"],
    )
    assert my_sess_res.status_code == 404


def test_admin_publish_session_and_student_marksheet_access(client, admin_headers, setup_published_env):
    """Publishing enables student marksheet access; withholding securely masks sensitive data."""
    env = setup_published_env
    session_id = env["session_id"]

    # 1. Withhold Bob's result first (while session is calculated)
    bob_res = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/students/{env['s2_id']}",
        headers=admin_headers,
    )
    bob_result_id = bob_res.json()["id"]
    client.patch(
        f"{settings.API_V1_PREFIX}/results/{bob_result_id}/withhold",
        json={"is_withheld": True, "reason": "Tuition fee dues pending"},
        headers=admin_headers,
    )

    # 2. Publish Examination Session (Admin)
    pub_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/publish",
        headers=admin_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == SessionStatus.PUBLISHED.value

    # 3. Alice (Passed Student) views her marksheet
    alice_res = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=env["s1_headers"],
    )
    assert alice_res.status_code == 200
    alice_sheets = alice_res.json()
    assert len(alice_sheets) == 1

    sheet = alice_sheets[0]
    assert sheet["registration_number"] == env["reg1"]
    assert sheet["is_withheld"] is False
    assert sheet["total_marks_obtained"] == 180.0
    assert sheet["total_max_marks"] == 200.0
    assert sheet["percentage"] == 90.0
    assert sheet["result_status"] == ResultStatus.PASS.value
    assert len(sheet["subjects"]) == 2
    for s in sheet["subjects"]:
        assert s["is_passed"] is True

    # 4. Bob (Withheld Student) views his marksheet -> Masked!
    bob_view = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=env["s2_headers"],
    )
    assert bob_view.status_code == 200
    bob_sheets = bob_view.json()
    assert len(bob_sheets) == 1

    bob_sheet = bob_sheets[0]
    assert bob_sheet["registration_number"] == env["reg2"]
    assert bob_sheet["is_withheld"] is True
    # Marks and percentage must be masked to None / empty
    assert bob_sheet["total_marks_obtained"] is None
    assert bob_sheet["percentage"] is None
    assert bob_sheet["result_status"] is None
    assert bob_sheet["subjects"] == []
    assert "withheld" in bob_sheet["notice"].lower()

    # 5. Administrative Rollback / Unpublish
    unpub_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/unpublish",
        json={"is_withheld": False, "reason": "Discovered grading calibration error"},
        headers=admin_headers,
    )
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == SessionStatus.CALCULATED.value

    # After unpublish, Alice can no longer view her results
    alice_after_unpub = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=env["s1_headers"],
    )
    assert alice_after_unpub.status_code == 200
    assert alice_after_unpub.json() == []
