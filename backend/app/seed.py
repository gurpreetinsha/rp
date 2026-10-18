"""Database seed script for populating realistic academic data and demo accounts."""

import uuid
from sqlalchemy import select
from app.database import SessionLocal, engine, Base
import app.models  # Registers all models with Base
from app.core.enums import UserRole, SessionStatus, BatchStatus, ResultStatus
from app.core.security import get_password_hash
from app.core.models_base import utcnow
from app.modules.auth.models import User
from app.modules.academic.models import Department, Program, Course, ExaminationSession
from app.modules.users_mgmt.models import Teacher, Student, CourseEnrollment, TeacherCourseAssignment
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.marks.models import OfficialMark
from app.modules.results.models import CalculatedResult, ResultSubjectDetail
from app.modules.audit.service import AuditService


def seed_database():
    print("[SEED] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_admin = db.execute(
            select(User).where(User.email == "admin@institution.edu")
        ).scalar_one_or_none()

        if existing_admin:
            print("[INFO] Database is already seeded. Ready for use.")
            return

        print("[INFO] Seeding Academic Entities and User Accounts...")

        # 1. Admin User
        admin_user = User(
            email="admin@institution.edu",
            hashed_password=get_password_hash("AdminSecret123!"),
            full_name="Dr. Sarah Connor (Registrar & Admin)",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        db.flush()

        # 2. Departments & Programs
        dept_cs = Department(
            code="CSE",
            name="Department of Computer Science & Engineering",
        )
        dept_it = Department(
            code="IT",
            name="Department of Information Technology",
        )
        db.add_all([dept_cs, dept_it])
        db.flush()

        prog_cs = Program(
            department_id=dept_cs.id,
            code="BTECH-CSE",
            name="Bachelor of Technology in Computer Science & Engineering",
            total_semesters=8,
        )
        db.add(prog_cs)
        db.flush()

        # 3. Courses
        c1 = Course(
            code="CS301",
            name="Data Structures & Algorithms",
            credits=4.0,
            pass_percentage=40.0,
            is_active=True,
        )
        c2 = Course(
            code="CS302",
            name="Database Management Systems",
            credits=4.0,
            pass_percentage=40.0,
            is_active=True,
        )
        c3 = Course(
            code="CS303",
            name="Operating Systems",
            credits=3.0,
            pass_percentage=40.0,
            is_active=True,
        )
        db.add_all([c1, c2, c3])
        db.flush()

        # 4. Teacher User & Profile
        teacher_user = User(
            email="teacher@institution.edu",
            hashed_password=get_password_hash("TeacherSecret123!"),
            full_name="Prof. Alan Turing",
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(teacher_user)
        db.flush()

        teacher_profile = Teacher(
            user_id=teacher_user.id,
            employee_id="FAC-001",
            department_id=dept_cs.id,
            designation="Senior Professor of Computing",
        )
        db.add(teacher_profile)
        db.flush()

        # 5. Student Users & Profiles
        student_configs = [
            ("student@institution.edu", "Alice Smith", "STU-2026-001"),
            ("student2@institution.edu", "Bob Jones", "STU-2026-002"),
            ("student3@institution.edu", "Charlie Brown", "STU-2026-003"),
        ]
        students = []
        for email, name, reg in student_configs:
            u = User(
                email=email,
                hashed_password=get_password_hash("StudentSecret123!"),
                full_name=name,
                role=UserRole.STUDENT,
                is_active=True,
            )
            db.add(u)
            db.flush()

            st = Student(
                user_id=u.id,
                registration_number=reg,
                roll_number=f"R-{reg[-3:]}",
                program_id=prog_cs.id,
                current_semester=6,
            )
            db.add(st)
            db.flush()
            students.append(st)

        # 6. Session 1: Published Spring 2026 End-Semester Examinations
        sess1 = ExaminationSession(
            name="Spring 2026 End-Semester Examinations",
            academic_year="2025-2026",
            semester_number=6,
            status=SessionStatus.PUBLISHED,
            published_at=utcnow(),
            published_by_user_id=admin_user.id,
        )
        db.add(sess1)
        db.flush()

        # Enrollments & Assignments for Session 1
        for st in students:
            for c in [c1, c2, c3]:
                db.add(CourseEnrollment(student_id=st.id, course_id=c.id, session_id=sess1.id))

        for c in [c1, c2, c3]:
            db.add(TeacherCourseAssignment(teacher_id=teacher_profile.id, course_id=c.id, session_id=sess1.id))
        db.flush()

        # Create Approved Import Batch and Official Marks for Session 1
        dummy_batch = MarkImportBatch(
            session_id=sess1.id,
            course_id=c1.id,
            uploaded_by_teacher_id=teacher_profile.id,
            file_name="spring2026_final_marks.csv",
            file_hash="dummyhash_seed_spring2026",
            max_marks=100.0,
            status=BatchStatus.IMPORTED,
            total_rows=3,
            valid_rows=3,
            error_rows=0,
            reviewed_by_admin_id=admin_user.id,
            reviewed_at=utcnow(),
        )
        db.add(dummy_batch)
        db.flush()

        # Mark distributions
        # Alice (PASS): 88.0, 92.0, 85.0
        # Bob (WITHHELD): 78.0, 82.0, 75.0
        # Charlie (FAIL - ABSENT in CS302): 65.0, AB (0), 70.0
        marks_data = [
            (students[0], c1, 88.0, False),
            (students[0], c2, 92.0, False),
            (students[0], c3, 85.0, False),

            (students[1], c1, 78.0, False),
            (students[1], c2, 82.0, False),
            (students[1], c3, 75.0, False),

            (students[2], c1, 65.0, False),
            (students[2], c2, 0.0, True),  # Absent!
            (students[2], c3, 70.0, False),
        ]

        for st, c, obtained, is_abs in marks_data:
            om = OfficialMark(
                session_id=sess1.id,
                course_id=c.id,
                student_id=st.id,
                batch_id=dummy_batch.id,
                marks_obtained=obtained,
                max_marks=100.0,
                is_absent=is_abs,
                is_amended=False,
            )
            db.add(om)
        db.flush()

        # 7. Calculate and populate CalculatedResult for Session 1
        # Alice
        cr1 = CalculatedResult(
            session_id=sess1.id,
            student_id=students[0].id,
            total_marks_obtained=265.0,
            total_max_marks=300.0,
            percentage=88.33,
            result_status=ResultStatus.PASS,
            is_withheld=False,
            calculated_at=utcnow(),
        )
        db.add(cr1)
        db.flush()
        db.add_all([
            ResultSubjectDetail(calculated_result_id=cr1.id, course_id=c1.id, marks_obtained=88.0, max_marks=100.0, percentage=88.0, is_absent=False, is_passed=True, remarks="PASS"),
            ResultSubjectDetail(calculated_result_id=cr1.id, course_id=c2.id, marks_obtained=92.0, max_marks=100.0, percentage=92.0, is_absent=False, is_passed=True, remarks="PASS"),
            ResultSubjectDetail(calculated_result_id=cr1.id, course_id=c3.id, marks_obtained=85.0, max_marks=100.0, percentage=85.0, is_absent=False, is_passed=True, remarks="PASS"),
        ])

        # Bob (Withheld)
        cr2 = CalculatedResult(
            session_id=sess1.id,
            student_id=students[1].id,
            total_marks_obtained=235.0,
            total_max_marks=300.0,
            percentage=78.33,
            result_status=ResultStatus.PASS,
            is_withheld=True,  # Withheld for demo demonstration!
            calculated_at=utcnow(),
        )
        db.add(cr2)
        db.flush()
        db.add_all([
            ResultSubjectDetail(calculated_result_id=cr2.id, course_id=c1.id, marks_obtained=78.0, max_marks=100.0, percentage=78.0, is_absent=False, is_passed=True, remarks="PASS"),
            ResultSubjectDetail(calculated_result_id=cr2.id, course_id=c2.id, marks_obtained=82.0, max_marks=100.0, percentage=82.0, is_absent=False, is_passed=True, remarks="PASS"),
            ResultSubjectDetail(calculated_result_id=cr2.id, course_id=c3.id, marks_obtained=75.0, max_marks=100.0, percentage=75.0, is_absent=False, is_passed=True, remarks="PASS"),
        ])

        # Charlie (Fail due to absentee)
        cr3 = CalculatedResult(
            session_id=sess1.id,
            student_id=students[2].id,
            total_marks_obtained=135.0,
            total_max_marks=300.0,
            percentage=45.0,
            result_status=ResultStatus.FAIL,
            is_withheld=False,
            calculated_at=utcnow(),
        )
        db.add(cr3)
        db.flush()
        db.add_all([
            ResultSubjectDetail(calculated_result_id=cr3.id, course_id=c1.id, marks_obtained=65.0, max_marks=100.0, percentage=65.0, is_absent=False, is_passed=True, remarks="PASS"),
            ResultSubjectDetail(calculated_result_id=cr3.id, course_id=c2.id, marks_obtained=0.0, max_marks=100.0, percentage=0.0, is_absent=True, is_passed=False, remarks="ABSENT"),
            ResultSubjectDetail(calculated_result_id=cr3.id, course_id=c3.id, marks_obtained=70.0, max_marks=100.0, percentage=70.0, is_absent=False, is_passed=True, remarks="PASS"),
        ])

        # 8. Session 2: Active Fall 2026 Regular Semester (MARKS_ENTRY_OPEN)
        sess2 = ExaminationSession(
            name="Fall 2026 Regular Semester Examinations",
            academic_year="2026-2027",
            semester_number=5,
            status=SessionStatus.MARKS_ENTRY_OPEN,
        )
        db.add(sess2)
        db.flush()

        for st in students:
            for c in [c1, c2]:
                db.add(CourseEnrollment(student_id=st.id, course_id=c.id, session_id=sess2.id))

        for c in [c1, c2]:
            db.add(TeacherCourseAssignment(teacher_id=teacher_profile.id, course_id=c.id, session_id=sess2.id))

        # Initial Audit Log
        AuditService.log(
            db=db,
            user_id=admin_user.id,
            action="SYSTEM_INITIALIZED",
            entity_type="system",
            entity_id="init",
            details={"demo_records_created": 3, "sessions": 2},
        )

        db.commit()
        print("[SUCCESS] Database successfully seeded with demo accounts and examination records!")
        print("  - Admin:   admin@institution.edu   / AdminSecret123!")
        print("  - Teacher: teacher@institution.edu / TeacherSecret123!")
        print("  - Student: student@institution.edu / StudentSecret123!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
