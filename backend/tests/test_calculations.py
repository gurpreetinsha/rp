import io
import uuid
import pytest
from app.config import settings
from app.core.enums import SessionStatus, ResultStatus, UserRole
from app.core.security import create_access_token


@pytest.fixture
def setup_calculation_env(client, admin_headers):
    """Sets up a comprehensive academic session with 2 courses and 3 students with approved official marks."""
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

    # 2. Examination Session
    session_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/sessions",
        json={
            "name": f"Session_{uuid.uuid4().hex[:6]}",
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

    # 3. Two Courses
    # Course A: pass_percentage = 40.0
    c1_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={
            "code": f"CS_{uuid.uuid4().hex[:6].upper()}",
            "name": "Algorithms",
            "credits": 4.0,
            "pass_percentage": 40.0,
        },
        headers=admin_headers,
    )
    c1_id = c1_res.json()["id"]

    # Course B: pass_percentage = 50.0
    c2_res = client.post(
        f"{settings.API_V1_PREFIX}/academic/courses",
        json={
            "code": f"CS_{uuid.uuid4().hex[:6].upper()}",
            "name": "Database Systems",
            "credits": 3.0,
            "pass_percentage": 50.0,
        },
        headers=admin_headers,
    )
    c2_id = c2_res.json()["id"]

    # 4. Teacher + Course Assignments
    t_res = client.post(
        f"{settings.API_V1_PREFIX}/users-mgmt/teachers",
        json={
            "email": f"prof_{uuid.uuid4().hex[:6]}@institution.edu",
            "password": "Password123!",
            "full_name": "Prof. Alan Turing",
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

    # 5. Three Students
    reg_numbers = [
        f"STU_{uuid.uuid4().hex[:6].upper()}",
        f"STU_{uuid.uuid4().hex[:6].upper()}",
        f"STU_{uuid.uuid4().hex[:6].upper()}",
    ]
    student_ids = []
    student_user_ids = []

    for idx, reg in enumerate(reg_numbers):
        s_res = client.post(
            f"{settings.API_V1_PREFIX}/users-mgmt/students",
            json={
                "email": f"student_{reg.lower()}@institution.edu",
                "password": "Password123!",
                "full_name": f"Student {idx + 1}",
                "registration_number": reg,
                "program_id": prog_id,
            },
            headers=admin_headers,
        )
        student_ids.append(s_res.json()["id"])
        student_user_ids.append(s_res.json()["user_id"])

        # Enroll in both courses
        client.post(
            f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
            json={"student_id": s_res.json()["id"], "course_id": c1_id, "session_id": session_id},
            headers=admin_headers,
        )
        client.post(
            f"{settings.API_V1_PREFIX}/users-mgmt/enrollments",
            json={"student_id": s_res.json()["id"], "course_id": c2_id, "session_id": session_id},
            headers=admin_headers,
        )

    student_token = create_access_token(data={"sub": str(student_user_ids[0]), "role": UserRole.STUDENT.value})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    return {
        "session_id": session_id,
        "c1_id": c1_id,
        "c2_id": c2_id,
        "teacher_headers": teacher_headers,
        "student_headers": student_headers,
        "reg_numbers": reg_numbers,
        "student_ids": student_ids,
    }


def test_calculate_role_enforcement(client, admin_headers, setup_calculation_env):
    """Teachers and students cannot trigger result calculations."""
    env = setup_calculation_env
    session_id = env["session_id"]

    # Teacher denied
    t_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        headers=env["teacher_headers"],
    )
    assert t_res.status_code == 403

    # Student denied
    s_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        headers=env["student_headers"],
    )
    assert s_res.status_code == 403


def test_calculate_missing_marks_fails_without_allow_partial(client, admin_headers, setup_calculation_env):
    """Result calculation must fail if course enrollments lack approved official marks."""
    env = setup_calculation_env
    session_id = env["session_id"]
    c1_id = env["c1_id"]
    t_headers = env["teacher_headers"]
    reg = env["reg_numbers"]

    # Upload and approve marks for Course 1 ONLY
    csv_content = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg[0]},Student 1,80.0,NO,\n"
        f"{reg[1]},Student 2,70.0,NO,\n"
        f"{reg[2]},Student 3,60.0,NO,\n"
    )
    up_res = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(c1_id), "max_marks": "100.0"},
        files={"file": ("c1_marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=t_headers,
    )
    assert up_res.status_code == 201
    batch_id = up_res.json()["id"]

    # Approve batch 1
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{batch_id}/approve",
        headers=admin_headers,
    )

    # Attempting to calculate results should fail because Course 2 has no approved marks
    calc_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        json={"allow_partial": False},
        headers=admin_headers,
    )
    assert calc_res.status_code == 422
    assert "lack official approved marks" in calc_res.json()["error"]["message"]


def test_complete_calculation_evaluation_and_summary(client, admin_headers, setup_calculation_env):
    """Tests end-to-end calculation: pass/fail evaluation, percentage math, and metrics."""
    env = setup_calculation_env
    session_id = env["session_id"]
    c1_id = env["c1_id"]
    c2_id = env["c2_id"]
    t_headers = env["teacher_headers"]
    reg = env["reg_numbers"]
    student_ids = env["student_ids"]

    # 1. Upload & Approve Course 1 (Algorithms, pass_pct=40)
    # Student 1: 75/100 (Pass)
    # Student 2: 85/100 (Pass)
    # Student 3: 60/100 (Pass)
    csv1 = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg[0]},Student 1,75.0,NO,\n"
        f"{reg[1]},Student 2,85.0,NO,\n"
        f"{reg[2]},Student 3,60.0,NO,\n"
    )
    up1 = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(c1_id), "max_marks": "100.0"},
        files={"file": ("c1.csv", io.BytesIO(csv1.encode("utf-8")), "text/csv")},
        headers=t_headers,
    )
    assert up1.status_code == 201
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{up1.json()['id']}/approve",
        headers=admin_headers,
    )

    # 2. Upload & Approve Course 2 (Database Systems, pass_pct=50)
    # Student 1: 85/100 (Pass) -> Overall: (75+85)/200 = 80.0%, PASS
    # Student 2: AB (Absent) -> Overall: FAIL
    # Student 3: 40/100 (<50% -> Fail subject) -> Overall: FAIL
    csv2 = (
        "registration_number,student_name,marks_obtained,is_absent,remarks\n"
        f"{reg[0]},Student 1,85.0,NO,\n"
        f"{reg[1]},Student 2,,YES,Medical leave\n"
        f"{reg[2]},Student 3,40.0,NO,\n"
    )
    up2 = client.post(
        f"{settings.API_V1_PREFIX}/imports/upload",
        data={"session_id": str(session_id), "course_id": str(c2_id), "max_marks": "100.0"},
        files={"file": ("c2.csv", io.BytesIO(csv2.encode("utf-8")), "text/csv")},
        headers=t_headers,
    )
    assert up2.status_code == 201
    client.post(
        f"{settings.API_V1_PREFIX}/imports/batches/{up2.json()['id']}/approve",
        headers=admin_headers,
    )

    # 3. Calculate Results (Admin)
    calc_res = client.post(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/calculate",
        headers=admin_headers,
    )
    assert calc_res.status_code == 200
    summary = calc_res.json()

    assert summary["total_students_enrolled"] == 3
    assert summary["total_students_evaluated"] == 3
    assert summary["total_passed"] == 1
    assert summary["total_failed"] == 2
    assert summary["total_withheld"] == 0
    assert summary["overall_pass_percentage"] == 33.33
    assert summary["status"] == SessionStatus.CALCULATED.value

    # 4. Check Individual Student Results
    # Student 1: PASS
    s1_res = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/students/{student_ids[0]}",
        headers=admin_headers,
    )
    assert s1_res.status_code == 200
    s1_data = s1_res.json()
    assert s1_data["total_marks_obtained"] == 160.0
    assert s1_data["total_max_marks"] == 200.0
    assert s1_data["percentage"] == 80.0
    assert s1_data["result_status"] == ResultStatus.PASS.value
    assert len(s1_data["subject_details"]) == 2
    for sub in s1_data["subject_details"]:
        assert sub["is_passed"] is True
        assert sub["is_absent"] is False

    # Student 2: FAIL due to absentee in Course 2
    s2_res = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/students/{student_ids[1]}",
        headers=admin_headers,
    )
    s2_data = s2_res.json()
    assert s2_data["result_status"] == ResultStatus.FAIL.value
    # Find Course 2 breakdown
    c2_detail = next(sd for sd in s2_data["subject_details"] if sd["course_id"] == c2_id)
    assert c2_detail["is_absent"] is True
    assert c2_detail["is_passed"] is False
    assert c2_detail["remarks"] == "ABSENT"

    # Student 3: FAIL due to marks (40) < pass_percentage (50) in Course 2
    s3_res = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/students/{student_ids[2]}",
        headers=admin_headers,
    )
    s3_data = s3_res.json()
    assert s3_data["result_status"] == ResultStatus.FAIL.value
    c2_detail_s3 = next(sd for sd in s3_data["subject_details"] if sd["course_id"] == c2_id)
    assert c2_detail_s3["is_absent"] is False
    assert c2_detail_s3["is_passed"] is False
    assert c2_detail_s3["remarks"] == "FAIL"

    # 5. Teacher can view summary & student list
    t_sum = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/summary",
        headers=t_headers,
    )
    assert t_sum.status_code == 200
    assert t_sum.json()["total_passed"] == 1

    t_list = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/students?result_status=PASS",
        headers=t_headers,
    )
    assert t_list.status_code == 200
    assert len(t_list.json()) == 1
    assert t_list.json()[0]["registration_number"] == reg[0]

    # 6. Withhold Student 1's Result (Admin)
    result_id = s1_data["id"]
    w_res = client.patch(
        f"{settings.API_V1_PREFIX}/results/{result_id}/withhold",
        json={"is_withheld": True, "reason": "Administrative inquiry pending"},
        headers=admin_headers,
    )
    assert w_res.status_code == 200
    assert w_res.json()["is_withheld"] is True

    # Check updated summary reflects withheld count
    w_sum = client.get(
        f"{settings.API_V1_PREFIX}/results/sessions/{session_id}/summary",
        headers=admin_headers,
    )
    assert w_sum.json()["total_withheld"] == 1

    # Release withheld result
    rel_res = client.patch(
        f"{settings.API_V1_PREFIX}/results/{result_id}/withhold",
        json={"is_withheld": False, "reason": "Cleared by academic committee"},
        headers=admin_headers,
    )
    assert rel_res.status_code == 200
    assert rel_res.json()["is_withheld"] is False
