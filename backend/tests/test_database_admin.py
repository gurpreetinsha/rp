import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.enums import SessionStatus


def test_academic_delete_and_session_update(client: TestClient, admin_headers: dict):
    # 1. Create Department
    dept_res = client.post(
        "/api/v1/academic/departments",
        json={"code": "PHY", "name": "Department of Physics"},
        headers=admin_headers,
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    # 2. Create Program
    prog_res = client.post(
        "/api/v1/academic/programs",
        json={"department_id": dept_id, "code": "BSC_PHY", "name": "B.Sc Physics", "total_semesters": 6},
        headers=admin_headers,
    )
    assert prog_res.status_code == 201
    prog_id = prog_res.json()["id"]

    # 3. Create Course
    course_res = client.post(
        "/api/v1/academic/courses",
        json={"code": "PHY101", "name": "Classical Mechanics", "credits": 4.0, "pass_percentage": 40.0},
        headers=admin_headers,
    )
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # 4. Create Session
    sess_res = client.post(
        "/api/v1/academic/sessions",
        json={"name": "Autumn 2026", "academic_year": "2026-2027", "semester_number": 1},
        headers=admin_headers,
    )
    assert sess_res.status_code == 201
    sess_id = sess_res.json()["id"]

    # 5. Update Session details
    upd_sess = client.patch(
        f"/api/v1/academic/sessions/{sess_id}",
        json={"name": "Autumn 2026 Updated", "semester_number": 2},
        headers=admin_headers,
    )
    assert upd_sess.status_code == 200
    assert upd_sess.json()["name"] == "Autumn 2026 Updated"
    assert upd_sess.json()["semester_number"] == 2

    # 6. Delete Course
    del_course = client.delete(f"/api/v1/academic/courses/{course_id}", headers=admin_headers)
    assert del_course.status_code == 200

    # 7. Delete Program
    del_prog = client.delete(f"/api/v1/academic/programs/{prog_id}", headers=admin_headers)
    assert del_prog.status_code == 200

    # 8. Delete Department
    del_dept = client.delete(f"/api/v1/academic/departments/{dept_id}", headers=admin_headers)
    assert del_dept.status_code == 200

    # 9. Delete Session
    del_sess = client.delete(f"/api/v1/academic/sessions/{sess_id}", headers=admin_headers)
    assert del_sess.status_code == 200


def test_users_mgmt_update_and_delete(client: TestClient, admin_headers: dict):
    # Setup department & program
    dept_res = client.post(
        "/api/v1/academic/departments",
        json={"code": "CHEM", "name": "Department of Chemistry"},
        headers=admin_headers,
    )
    dept_id = dept_res.json()["id"]

    prog_res = client.post(
        "/api/v1/academic/programs",
        json={"department_id": dept_id, "code": "BSC_CHEM", "name": "B.Sc Chemistry", "total_semesters": 6},
        headers=admin_headers,
    )
    prog_id = prog_res.json()["id"]

    # 1. Create Teacher
    teacher_res = client.post(
        "/api/v1/users-mgmt/teachers",
        json={
            "email": "dr.curie@institution.edu",
            "password": "Password123!",
            "full_name": "Dr. Marie Curie",
            "employee_id": "EMPCHEM01",
            "department_id": dept_id,
            "designation": "Professor",
        },
        headers=admin_headers,
    )
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    # 2. Update Teacher
    upd_teacher = client.patch(
        f"/api/v1/users-mgmt/teachers/{teacher_id}",
        json={"full_name": "Prof. Marie Curie", "designation": "Senior Professor"},
        headers=admin_headers,
    )
    assert upd_teacher.status_code == 200
    assert upd_teacher.json()["full_name"] == "Prof. Marie Curie"
    assert upd_teacher.json()["designation"] == "Senior Professor"

    # 3. Create Student
    student_res = client.post(
        "/api/v1/users-mgmt/students",
        json={
            "email": "student.marie@institution.edu",
            "password": "Password123!",
            "full_name": "Student Marie",
            "registration_number": "REGCHEM001",
            "roll_number": "CH-01",
            "program_id": prog_id,
            "current_semester": 1,
        },
        headers=admin_headers,
    )
    assert student_res.status_code == 201
    student_id = student_res.json()["id"]

    # 4. Update Student
    upd_student = client.patch(
        f"/api/v1/users-mgmt/students/{student_id}",
        json={"full_name": "Marie Student", "current_semester": 2},
        headers=admin_headers,
    )
    assert upd_student.status_code == 200
    assert upd_student.json()["full_name"] == "Marie Student"
    assert upd_student.json()["current_semester"] == 2

    # 5. Delete Student
    del_student = client.delete(f"/api/v1/users-mgmt/students/{student_id}", headers=admin_headers)
    assert del_student.status_code == 200

    # 6. Delete Teacher
    del_teacher = client.delete(f"/api/v1/users-mgmt/teachers/{teacher_id}", headers=admin_headers)
    assert del_teacher.status_code == 200


def test_database_admin_endpoints(client: TestClient, admin_headers: dict, teacher_headers: dict):
    # Non-admin access should be forbidden
    forbidden_res = client.get("/api/v1/database/tables", headers=teacher_headers)
    assert forbidden_res.status_code == 403

    # 1. List Tables
    tables_res = client.get("/api/v1/database/tables", headers=admin_headers)
    assert tables_res.status_code == 200
    tables = tables_res.json()
    assert isinstance(tables, list)
    table_names = [t["name"] for t in tables]
    assert "users" in table_names
    assert "academic_departments" in table_names

    # 2. Get rows from users table
    rows_res = client.get("/api/v1/database/tables/users/rows?page=1&limit=10", headers=admin_headers)
    assert rows_res.status_code == 200
    data = rows_res.json()
    assert data["table_name"] == "users"
    assert len(data["rows"]) > 0

    # 3. Insert row directly via DB Admin
    test_code = f"BIO_{uuid.uuid4().hex[:6].upper()}"
    insert_res = client.post(
        "/api/v1/database/tables/academic_departments/rows",
        json={"data": {"id": str(uuid.uuid4()), "code": test_code, "name": "Biology Dept", "is_active": True}},
        headers=admin_headers,
    )
    assert insert_res.status_code == 201

    # 4. Search rows in academic_departments
    search_res = client.get(
        f"/api/v1/database/tables/academic_departments/rows?search={test_code}",
        headers=admin_headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_rows"] >= 1
    found_row = [r for r in search_data["rows"] if r["code"] == test_code][0]
    row_id = found_row["id"]

    # 5. Update row directly via DB Admin
    update_res = client.put(
        f"/api/v1/database/tables/academic_departments/rows/{row_id}",
        json={"data": {"name": "Advanced Biology Department"}},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Advanced Biology Department"

    # 6. Execute SQL Query (SELECT)
    sql_sel = client.post(
        "/api/v1/database/query",
        json={"query": f"SELECT code, name FROM academic_departments WHERE code = '{test_code}'"},
        headers=admin_headers,
    )
    assert sql_sel.status_code == 200
    sel_json = sql_sel.json()
    assert sel_json["is_select"] is True
    assert len(sel_json["rows"]) == 1
    assert sel_json["rows"][0]["name"] == "Advanced Biology Department"

    # 7. Execute SQL Query (DML UPDATE)
    sql_dml = client.post(
        "/api/v1/database/query",
        json={"query": f"UPDATE academic_departments SET name = 'Cell Biology' WHERE code = '{test_code}'"},
        headers=admin_headers,
    )
    assert sql_dml.status_code == 200
    dml_json = sql_dml.json()
    assert dml_json["is_select"] is False
    assert dml_json["rows_affected"] == 1

    # 8. Delete row directly via DB Admin
    del_res = client.delete(
        f"/api/v1/database/tables/academic_departments/rows/{row_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 200

    # 9. Verify row is gone
    verify_res = client.get(
        f"/api/v1/database/tables/academic_departments/rows?search={test_code}",
        headers=admin_headers,
    )
    assert verify_res.json()["total_rows"] == 0
