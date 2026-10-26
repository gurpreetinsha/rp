import io
import uuid
import pytest
from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.users_mgmt.models import Teacher, Student, CourseEnrollment, TeacherCourseAssignment
from app.modules.marks.models import OfficialMark
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.results.models import CalculatedResult
from app.core.enums import SessionStatus, ResultStatus, BatchStatus
from app.core.security import create_access_token


def test_security_headers_present(client):
    """Verify security headers middleware injects required defenses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_login_rate_limiting(client, student_user):
    """Verify that 5 failed login attempts trigger HTTP 429 Rate Limited."""
    for _ in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": student_user.email, "password": "WrongPassword123!"},
        )
        assert resp.status_code == 401

    # 6th attempt within the 60s rate limit window should receive 429
    resp_rate_limited = client.post(
        "/api/v1/auth/login",
        json={"email": student_user.email, "password": "WrongPassword123!"},
    )
    assert resp_rate_limited.status_code == 429
    assert "Too many failed login attempts" in resp_rate_limited.json()["error"]["message"]


def test_withholding_preserved_across_multiple_recalculations(client, db_session, admin_headers):
    """
    DATA-01 REGRESSION TEST:
    Calculate results -> withhold a student result -> recalculate multiple times.
    Withholding status must be reliably preserved across recalculations.
    """
    # 1. Setup session, department, program, course
    dept = Department(id=uuid.uuid4(), code=f"D_{uuid.uuid4().hex[:6].upper()}", name="Test Department")
    db_session.add(dept)
    db_session.flush()

    prog = Program(id=uuid.uuid4(), department_id=dept.id, code=f"P_{uuid.uuid4().hex[:6].upper()}", name="Test Program", total_semesters=8)
    db_session.add(prog)

    course = Course(id=uuid.uuid4(), code=f"C_{uuid.uuid4().hex[:6].upper()}", name="Intro to CS", credits=3.0, pass_percentage=40.0)
    db_session.add(course)

    session = ExaminationSession(
        id=uuid.uuid4(),
        name="Autumn 2026 Test",
        academic_year="2026-2027",
        semester_number=1,
        status=SessionStatus.MARKS_LOCKED,
    )
    db_session.add(session)
    db_session.flush()

    # 2. Setup Teacher and Student
    from app.modules.auth.models import User
    from app.core.enums import UserRole
    user_t = User(
        id=uuid.uuid4(),
        email=f"teacher_{uuid.uuid4().hex[:6]}@institution.edu",
        hashed_password="hash",
        full_name="Teacher Calc",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user_t)
    db_session.flush()

    teacher_prof = Teacher(
        id=uuid.uuid4(),
        user_id=user_t.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6].upper()}",
        department_id=dept.id,
    )
    db_session.add(teacher_prof)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        email=f"withhold_{uuid.uuid4().hex[:6]}@institution.edu",
        hashed_password="hash",
        full_name="Withheld Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    student = Student(
        id=uuid.uuid4(),
        user_id=user.id,
        registration_number=f"REG_{uuid.uuid4().hex[:6].upper()}",
        program_id=prog.id,
    )
    db_session.add(student)
    db_session.flush()

    # Create batch
    batch = MarkImportBatch(
        id=uuid.uuid4(),
        session_id=session.id,
        course_id=course.id,
        uploaded_by_teacher_id=teacher_prof.id,
        max_marks=100.0,
        file_name="marks.csv",
        file_hash=uuid.uuid4().hex,
        total_rows=1,
        valid_rows=1,
        error_rows=0,
        status=BatchStatus.IMPORTED,
    )
    db_session.add(batch)
    db_session.flush()

    # 3. Enrollment and official mark
    enrollment = CourseEnrollment(
        id=uuid.uuid4(),
        student_id=student.id,
        course_id=course.id,
        session_id=session.id,
    )
    db_session.add(enrollment)

    mark = OfficialMark(
        id=uuid.uuid4(),
        session_id=session.id,
        course_id=course.id,
        student_id=student.id,
        batch_id=batch.id,
        marks_obtained=85.0,
        max_marks=100.0,
        is_absent=False,
    )
    db_session.add(mark)
    db_session.commit()

    # 4. First calculation
    calc_resp = client.post(
        f"/api/v1/results/sessions/{session.id}/calculate",
        headers=admin_headers,
    )
    assert calc_resp.status_code == 200

    # Retrieve calculated result
    results = client.get(
        f"/api/v1/results/sessions/{session.id}/students",
        headers=admin_headers,
    ).json()
    assert len(results) == 1
    result_id = results[0]["id"]
    assert results[0]["is_withheld"] is False

    # 5. Admin withholds the result
    withhold_resp = client.patch(
        f"/api/v1/results/{result_id}/withhold",
        json={"is_withheld": True, "reason": "Administrative financial hold"},
        headers=admin_headers,
    )
    assert withhold_resp.status_code == 200
    assert withhold_resp.json()["is_withheld"] is True

    # 6. Recalculate 1st time - Withhold must be preserved!
    recalc_1 = client.post(
        f"/api/v1/results/sessions/{session.id}/calculate",
        headers=admin_headers,
    )
    assert recalc_1.status_code == 200

    results_after_1 = client.get(
        f"/api/v1/results/sessions/{session.id}/students",
        headers=admin_headers,
    ).json()
    assert len(results_after_1) == 1
    assert results_after_1[0]["is_withheld"] is True

    # 7. Recalculate 2nd and 3rd time
    for _ in range(2):
        recalc = client.post(
            f"/api/v1/results/sessions/{session.id}/calculate",
            headers=admin_headers,
        )
        assert recalc.status_code == 200

    results_after_3 = client.get(
        f"/api/v1/results/sessions/{session.id}/students",
        headers=admin_headers,
    ).json()
    assert len(results_after_3) == 1
    assert results_after_3[0]["is_withheld"] is True


def test_withholding_preserved_during_mark_amendment(client, db_session, admin_headers):
    """
    DATA-01 REGRESSION TEST:
    When a mark is amended for a student whose result is currently withheld,
    the recalculated result must remain withheld.
    """
    dept = Department(id=uuid.uuid4(), code=f"D_{uuid.uuid4().hex[:6].upper()}", name="Amend Dept")
    db_session.add(dept)
    db_session.flush()

    prog = Program(id=uuid.uuid4(), department_id=dept.id, code=f"P_{uuid.uuid4().hex[:6].upper()}", name="Amend Program", total_semesters=8)
    db_session.add(prog)

    course = Course(id=uuid.uuid4(), code=f"C_{uuid.uuid4().hex[:6].upper()}", name="Operating Systems", credits=4.0, pass_percentage=40.0)
    db_session.add(course)

    session = ExaminationSession(
        id=uuid.uuid4(),
        name="Spring 2026 Amend Session",
        academic_year="2025-2026",
        semester_number=2,
        status=SessionStatus.MARKS_LOCKED,
    )
    db_session.add(session)
    db_session.flush()

    from app.modules.auth.models import User
    from app.core.enums import UserRole
    user_t = User(
        id=uuid.uuid4(),
        email=f"teacher_am_{uuid.uuid4().hex[:6]}@institution.edu",
        hashed_password="hash",
        full_name="Teacher Amend",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user_t)
    db_session.flush()

    teacher_prof = Teacher(
        id=uuid.uuid4(),
        user_id=user_t.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6].upper()}",
        department_id=dept.id,
    )
    db_session.add(teacher_prof)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        email=f"amend_{uuid.uuid4().hex[:6]}@institution.edu",
        hashed_password="hash",
        full_name="Amend Withhold Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    student = Student(
        id=uuid.uuid4(),
        user_id=user.id,
        registration_number=f"REG_{uuid.uuid4().hex[:6].upper()}",
        program_id=prog.id,
    )
    db_session.add(student)
    db_session.flush()

    batch = MarkImportBatch(
        id=uuid.uuid4(),
        session_id=session.id,
        course_id=course.id,
        uploaded_by_teacher_id=teacher_prof.id,
        max_marks=100.0,
        file_name="marks.csv",
        file_hash=uuid.uuid4().hex,
        total_rows=1,
        valid_rows=1,
        error_rows=0,
        status=BatchStatus.IMPORTED,
    )
    db_session.add(batch)
    db_session.flush()

    enrollment = CourseEnrollment(
        id=uuid.uuid4(),
        student_id=student.id,
        course_id=course.id,
        session_id=session.id,
    )
    db_session.add(enrollment)

    mark = OfficialMark(
        id=uuid.uuid4(),
        session_id=session.id,
        course_id=course.id,
        student_id=student.id,
        batch_id=batch.id,
        marks_obtained=35.0,
        max_marks=100.0,
        is_absent=False,
    )
    db_session.add(mark)
    db_session.commit()

    # Calculate initial results
    client.post(f"/api/v1/results/sessions/{session.id}/calculate", headers=admin_headers)

    res = client.get(f"/api/v1/results/sessions/{session.id}/students", headers=admin_headers).json()[0]
    result_id = res["id"]

    # Withhold the result
    client.patch(
        f"/api/v1/results/{result_id}/withhold",
        json={"is_withheld": True, "reason": "Disciplinary Inquiry"},
        headers=admin_headers,
    )

    # Amend the mark (from 35 to 75)
    amend_resp = client.post(
        f"/api/v1/marks/official/{mark.id}/amend",
        json={"new_marks_obtained": 75.0, "reason": "Scrutiny committee upward revision"},
        headers=admin_headers,
    )
    assert amend_resp.status_code == 200

    # Verify result in database remains withheld!
    res_after_amend = client.get(
        f"/api/v1/results/sessions/{session.id}/students",
        headers=admin_headers,
    ).json()[0]

    assert res_after_amend["is_withheld"] is True
    assert res_after_amend["total_marks_obtained"] == 75.0


def test_teacher_idor_enrollment_and_results(client, db_session):
    """
    SEC-03 REGRESSION TEST:
    Teacher A cannot inspect enrollments or results for courses/students assigned to Teacher B.
    """
    from app.modules.auth.models import User
    from app.core.enums import UserRole
    from app.core.security import hash_password

    dept = Department(id=uuid.uuid4(), code=f"D_{uuid.uuid4().hex[:6].upper()}", name="IDOR Dept")
    db_session.add(dept)
    db_session.flush()

    prog = Program(id=uuid.uuid4(), department_id=dept.id, code=f"P_{uuid.uuid4().hex[:6].upper()}", name="IDOR Prog", total_semesters=8)
    db_session.add(prog)

    course_a = Course(id=uuid.uuid4(), code=f"C_{uuid.uuid4().hex[:6].upper()}", name="Course A", credits=3.0, pass_percentage=40.0)
    course_b = Course(id=uuid.uuid4(), code=f"C_{uuid.uuid4().hex[:6].upper()}", name="Course B", credits=3.0, pass_percentage=40.0)
    db_session.add_all([course_a, course_b])

    session = ExaminationSession(
        id=uuid.uuid4(),
        name="IDOR Test Session",
        academic_year="2026-2027",
        semester_number=1,
    )
    db_session.add(session)
    db_session.flush()

    # Create Teacher A
    user_ta = User(id=uuid.uuid4(), email=f"ta_{uuid.uuid4().hex[:6]}@institution.edu", hashed_password=hash_password("Pass123!"), full_name="Teacher A", role=UserRole.TEACHER)
    db_session.add(user_ta)
    db_session.flush()
    prof_ta = Teacher(id=uuid.uuid4(), user_id=user_ta.id, employee_id=f"EMP_{uuid.uuid4().hex[:6].upper()}", department_id=dept.id)
    db_session.add(prof_ta)

    # Create Teacher B
    user_tb = User(id=uuid.uuid4(), email=f"tb_{uuid.uuid4().hex[:6]}@institution.edu", hashed_password=hash_password("Pass123!"), full_name="Teacher B", role=UserRole.TEACHER)
    db_session.add(user_tb)
    db_session.flush()
    prof_tb = Teacher(id=uuid.uuid4(), user_id=user_tb.id, employee_id=f"EMP_{uuid.uuid4().hex[:6].upper()}", department_id=dept.id)
    db_session.add(prof_tb)

    # Assign Teacher A to Course A only
    asgn_a = TeacherCourseAssignment(id=uuid.uuid4(), teacher_id=prof_ta.id, course_id=course_a.id, session_id=session.id)
    # Assign Teacher B to Course B only
    asgn_b = TeacherCourseAssignment(id=uuid.uuid4(), teacher_id=prof_tb.id, course_id=course_b.id, session_id=session.id)
    db_session.add_all([asgn_a, asgn_b])

    # Student 2 is enrolled only in Course B
    user_s2 = User(id=uuid.uuid4(), email=f"s2_{uuid.uuid4().hex[:6]}@institution.edu", hashed_password="h", full_name="Student 2", role=UserRole.STUDENT)
    db_session.add(user_s2)
    db_session.flush()
    stud_2 = Student(id=uuid.uuid4(), user_id=user_s2.id, registration_number=f"REG_{uuid.uuid4().hex[:6].upper()}", program_id=prog.id)
    db_session.add(stud_2)
    db_session.flush()

    enr_b = CourseEnrollment(id=uuid.uuid4(), student_id=stud_2.id, course_id=course_b.id, session_id=session.id)
    db_session.add(enr_b)
    db_session.commit()

    token_ta = create_access_token({"sub": str(user_ta.id), "role": user_ta.role.value})
    headers_ta = {"Authorization": f"Bearer {token_ta}"}

    # 1. Teacher A tries to query enrollments for Course B -> HTTP 403 Forbidden!
    resp_enr = client.get(
        f"/api/v1/users-mgmt/enrollments?session_id={session.id}&course_id={course_b.id}",
        headers=headers_ta,
    )
    assert resp_enr.status_code == 403
    assert "You are not assigned to evaluate this course" in resp_enr.json()["error"]["message"]

    # 2. Teacher A tries to query results for Student 2 (who is in Course B, not Course A) -> HTTP 403 Forbidden!
    resp_res = client.get(
        f"/api/v1/results/sessions/{session.id}/students/{stud_2.id}",
        headers=headers_ta,
    )
    assert resp_res.status_code == 403
    assert "You are not authorized to view results for this student" in resp_res.json()["error"]["message"]


def test_absentee_marks_column_handling(client, db_session, teacher_user, teacher_headers):
    """
    CSV VALIDATION TEST:
    Verify that entering 'AB' or 'ABSENT' in the marks column is correctly treated
    as is_absent=True with zero marks without triggering numeric parsing failures.
    """
    teacher_prof = db_session.query(Teacher).filter(Teacher.user_id == teacher_user.id).first()
    dept = db_session.query(Department).first()
    prog = Program(id=uuid.uuid4(), department_id=dept.id, code=f"P_{uuid.uuid4().hex[:6].upper()}", name="AB Prog", total_semesters=8)
    db_session.add(prog)

    course = Course(id=uuid.uuid4(), code=f"C_{uuid.uuid4().hex[:6].upper()}", name="AB Course", credits=3.0, pass_percentage=40.0)
    db_session.add(course)

    session = ExaminationSession(
        id=uuid.uuid4(),
        name="AB Session",
        academic_year="2026-2027",
        semester_number=1,
        status=SessionStatus.MARKS_ENTRY_OPEN,
    )
    db_session.add(session)
    db_session.flush()

    asgn = TeacherCourseAssignment(id=uuid.uuid4(), teacher_id=teacher_prof.id, course_id=course.id, session_id=session.id)
    db_session.add(asgn)

    # Create enrolled student
    from app.modules.auth.models import User
    from app.core.enums import UserRole
    user = User(id=uuid.uuid4(), email=f"ab_{uuid.uuid4().hex[:6]}@institution.edu", hashed_password="h", full_name="AB Stud", role=UserRole.STUDENT)
    db_session.add(user)
    db_session.flush()

    reg_no = f"REG_{uuid.uuid4().hex[:6].upper()}"
    student = Student(id=uuid.uuid4(), user_id=user.id, registration_number=reg_no, program_id=prog.id)
    db_session.add(student)
    db_session.flush()

    enr = CourseEnrollment(id=uuid.uuid4(), student_id=student.id, course_id=course.id, session_id=session.id)
    db_session.add(enr)
    db_session.commit()

    # CSV with 'AB' in marks_obtained column
    csv_content = f"registration_number,marks_obtained,is_absent\n{reg_no},AB,NO\n"
    files = {"file": ("marks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {
        "session_id": str(session.id),
        "course_id": str(course.id),
        "max_marks": "100.0",
    }

    resp = client.post("/api/v1/imports/upload", data=data, files=files, headers=teacher_headers)
    assert resp.status_code == 201
    batch_data = resp.json()
    assert batch_data["status"] == "PENDING_APPROVAL"
    assert batch_data["valid_rows"] == 1
    assert batch_data["error_rows"] == 0
