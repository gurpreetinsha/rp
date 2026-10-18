import io
import uuid
import pytest
from app.config import settings
from app.core.enums import SessionStatus, ResultStatus, UserRole
from app.core.security import create_access_token


@pytest.fixture
def setup_amendment_env(client, admin_headers):
    """Sets up a published session with 1 course and 1 student who initially failed."""
    dept_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json={"code": f"D_{uuid.uuid4().hex[:6].upper()}", "name": "Mechanical Engineering"},
        headers=admin_headers,
    )
    dept_id = dept_res.json()["id"]

    prog_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/programs",
        json={
            "department_id": dept_id,
            "code": f"P_{uuid.uuid4().hex[:6].upper()}",
            "name": "B.Tech Mechanical Engineering",
            "total_semesters": 8,
        },
        headers=admin_headers,
    )
    prog_id = prog_res.json()["id"]

    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": f"Session_{uuid.uuid4().hex[:6]}",
            "academic_year": "2026-2027",
            "semester_number": 3,
        },
        headers=admin_headers,
    )
    session_id = session_res.json()["id"]

    client.patch(
        f"{settings.API_V1_PREFIX}/academic/sessions/{session_id}/status",
        json={"status": SessionStatus.MARKS_ENTRY_OPEN.value},
        headers=admin_headers,
    )

    course_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={"code": f"ME_{uuid.uuid4().hex[:6].upper()}", "name": "Thermodynamics", "credits": 4.0, "pass_percentage": 40.0},
        headers=admin_headers,
    )
    course_id = course_res.json()["id"]

    # Teacher
    t_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": f"prof_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Prof. Sadi Carnot",
            "employee_id": f"T_{uuid.uuid4().hex[:6].upper()}",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    t_id = t_res.json()["id"]
    t_user_id = t_res.json()["user_id"]

    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/assignments",
        json={"teacher_id": t_id, "course_id": course_id, "session_id": session_id},
        headers=admin_headers,
    )
    teacher_token = create_access_token(data={"sub": str(t_user_id), "role": UserRole.TEACHER.value})
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Student
    reg = f"STU_{uuid.uuid4().hex[:6].upper()}"
    s_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/students",
        json={
            "email": f"stu_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "James Joule",
            "registration_number": reg,
            "program_id": prog_id,
        },
        headers=admin_headers,
    )
    student_id = s_res.json()["id"]
    student_user_id = s_res.json()["user_id"]

    client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
        json={"student_id": student_id, "course_id": course_id, "session_id": session_id},
        headers=admin_headers,
    )

    # Initial Upload: Student scored 35/100 (< 40% pass criteria -> FAIL)
    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg},James Joule,35.0,NO,Initial evaluation\n"
    )
    up_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(course_id), "max_marks": "100.0"},
        files={"file": ("thermo.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=teacher_headers,
    )
    batch_id = up_res.json()["id"]

    # Approve -> Official Mark
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve",
        headers=admin_headers,
    )

    # Calculate -> Student Result is FAIL
    client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        headers=admin_headers,
    )

    # Publish
    client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/publish",
        headers=admin_headers,
    )

    student_token = create_access_token(data={"sub": str(student_user_id), "role": UserRole.STUDENT.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Retrieve official mark ID
    marks_list = client.get(
        f"{settings.API_V1_PREFIX}/marks/official?session_id={session_id}&course_id={course_id}",
        headers=admin_headers,
    ).json()
    official_mark_id = marks_list[0]["id"]

    return {
        "session_id": session_id,
        "course_id": course_id,
        "student_id": student_id,
        "official_mark_id": official_mark_id,
        "student_headers": student_headers,
        "teacher_headers": teacher_headers,
        "reg": reg,
    }


def test_post_publication_amendment_recalculates_result(client, admin_headers, setup_amendment_env):
    """Admin amends a mark post-publication; verifies audit trail and dynamic result recalculation."""
    env = setup_amendment_env
    mark_id = env["official_mark_id"]
    s_headers = env["student_headers"]

    # Verify student initially sees FAIL
    initial_sheet = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=s_headers,
    ).json()[0]
    assert initial_sheet["result_status"] == ResultStatus.FAIL.value
    assert initial_sheet["percentage"] == 35.0

    # Non-admin cannot amend
    t_amend = client.post(
        f"{settings.API_V1_PREFIX}/marks/official/{mark_id}/amend",
        json={"new_marks_obtained": 65.0, "reason": "Re-evaluation after scrutiny"},
        headers=env["teacher_headers"],
    )
    assert t_amend.status_code == 403

    # Admin amends mark to 65.0 (Pass)
    amend_res = client.post(
        f"{settings.API_V1_PREFIX}/marks/official/{mark_id}/amend",
        json={"new_marks_obtained": 65.0, "new_is_absent": False, "reason": "Re-evaluation after scrutiny"},
        headers=admin_headers,
    )
    assert amend_res.status_code == 200
    amended_mark = amend_res.json()
    assert amended_mark["marks_obtained"] == 65.0
    assert amended_mark["is_amended"] is True

    # Check amendment history record
    history_res = client.get(
        f"{settings.API_V1_PREFIX}/marks/official/{mark_id}/amendments",
        headers=admin_headers,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["old_marks_obtained"] == 35.0
    assert history[0]["new_marks_obtained"] == 65.0
    assert history[0]["reason"] == "Re-evaluation after scrutiny"

    # Check student marksheet immediately reflects PASS and 65.0%
    updated_sheet = client.get(
        f"{settings.API_V1_PREFIX}/results/my-results",
        headers=s_headers,
    ).json()[0]
    assert updated_sheet["result_status"] == ResultStatus.PASS.value
    assert updated_sheet["percentage"] == 65.0
    assert updated_sheet["total_marks_obtained"] == 65.0
    assert updated_sheet["subjects"][0]["is_passed"] is True


def test_audit_logs_query(client, admin_headers, setup_amendment_env):
    """Admin can query audit logs; teachers and students are forbidden."""
    env = setup_amendment_env

    # Student denied
    s_audit = client.get(
        f"{settings.API_V1_PREFIX}/audit/logs",
        headers=env["student_headers"],
    )
    assert s_audit.status_code == 403

    # Teacher denied
    t_audit = client.get(
        f"{settings.API_V1_PREFIX}/audit/logs",
        headers=env["teacher_headers"],
    )
    assert t_audit.status_code == 403

    # Admin lists logs
    admin_audit = client.get(
        f"{settings.API_V1_PREFIX}/audit/logs?limit=20",
        headers=admin_headers,
    )
    assert admin_audit.status_code == 200
    logs = admin_audit.json()
    assert len(logs) > 0
    actions = [log["action"] for log in logs]
    assert "PUBLISH_SESSION_RESULTS" in actions or "CALCULATE_RESULTS" in actions
