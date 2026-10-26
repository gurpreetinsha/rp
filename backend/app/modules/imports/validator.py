import csv
import io
import hashlib
import uuid
from typing import List, Dict, Any, Tuple, Set
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.academic.models import ExaminationSession, Course
from app.modules.users_mgmt.models import Teacher, Student, CourseEnrollment, TeacherCourseAssignment
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.marks.models import OfficialMark
from app.core.enums import SessionStatus, BatchStatus
from app.core.exceptions import ValidationFailedException, ConflictException, ForbiddenException, NotFoundException

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class CSVValidationEngine:
    """Rigorous 12-step validation engine for teacher marks uploads."""

    REQUIRED_HEADERS = {"registration_number", "marks_obtained", "is_absent"}

    @staticmethod
    def validate_and_stage_csv(
        db: Session,
        session_id: uuid.UUID,
        course_id: uuid.UUID,
        teacher_id: uuid.UUID,
        max_marks: float,
        file_name: str,
        file_bytes: bytes,
    ) -> Tuple[MarkImportBatch, List[Dict[str, Any]]]:
        """Perform full validation and stage all rows into the database."""

        # 1. File size check
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValidationFailedException("File size exceeds maximum permitted limit of 5MB")

        if len(file_bytes) == 0:
            raise ValidationFailedException("Uploaded file is empty")

        # 2. Encoding check & SHA-256 computation
        try:
            content_str = file_bytes.decode("utf-8-sig")  # Handles optional UTF-8 BOM
        except UnicodeDecodeError:
            raise ValidationFailedException("File must be valid UTF-8 encoded text/CSV")

        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # 3. Session status check (must be MARKS_ENTRY_OPEN)
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")

        if session.status != SessionStatus.MARKS_ENTRY_OPEN:
            raise ValidationFailedException(
                f"Marks entry is not permitted for session in '{session.status.value}' status. "
                f"Session must be in '{SessionStatus.MARKS_ENTRY_OPEN.value}' status."
            )

        # 4. Course existence check
        course = db.get(Course, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} not found")

        # 5. Teacher assignment authorization check
        assignment = db.execute(
            select(TeacherCourseAssignment).where(
                TeacherCourseAssignment.teacher_id == teacher_id,
                TeacherCourseAssignment.course_id == course_id,
                TeacherCourseAssignment.session_id == session_id,
                TeacherCourseAssignment.is_active == True,
            )
        ).scalar_one_or_none()

        if not assignment:
            raise ForbiddenException(
                "You are not assigned to evaluate this course for this examination session."
            )

        # 6. Check existing official marks check
        existing_official = db.execute(
            select(OfficialMark).where(
                OfficialMark.session_id == session_id,
                OfficialMark.course_id == course_id,
            )
        ).first()

        if existing_official:
            raise ConflictException(
                "Official marks have already been imported for this course. "
                "Any modifications must follow the post-publication audited amendment workflow."
            )

        # 7. Duplicate file upload check
        existing_batch = db.execute(
            select(MarkImportBatch).where(
                MarkImportBatch.session_id == session_id,
                MarkImportBatch.course_id == course_id,
                MarkImportBatch.file_hash == file_hash,
                MarkImportBatch.status.in_([BatchStatus.PENDING_APPROVAL, BatchStatus.IMPORTED]),
            )
        ).scalar_one_or_none()

        if existing_batch:
            raise ConflictException(
                "An identical file has already been uploaded for this course and is currently pending review or imported."
            )

        # 8. CSV Parsing and Header Verification
        csv_file = io.StringIO(content_str)
        reader = csv.reader(csv_file)

        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValidationFailedException("CSV file contains no data or headers")

        headers = [h.strip().lower() for h in raw_headers]
        missing_headers = CSVValidationEngine.REQUIRED_HEADERS - set(headers)
        if missing_headers:
            raise ValidationFailedException(
                f"CSV is missing required columns: {', '.join(sorted(missing_headers))}. "
                f"Required: {', '.join(sorted(CSVValidationEngine.REQUIRED_HEADERS))}"
            )

        reg_idx = headers.index("registration_number")
        marks_idx = headers.index("marks_obtained")
        absent_idx = headers.index("is_absent")

        # 9. Read all rows and perform In-File Duplicate Check
        raw_rows = []
        reg_counts: Dict[str, List[int]] = {}

        for row_num, row in enumerate(reader, start=2):  # line 2 is first data row
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip blank lines

            reg_raw = row[reg_idx].strip() if reg_idx < len(row) else ""
            marks_raw = row[marks_idx].strip() if marks_idx < len(row) else ""
            absent_raw = row[absent_idx].strip() if absent_idx < len(row) else ""

            reg_normalized = reg_raw.upper()
            if reg_normalized:
                if reg_normalized not in reg_counts:
                    reg_counts[reg_normalized] = []
                reg_counts[reg_normalized].append(row_num)

            raw_rows.append({
                "row_number": row_num,
                "reg_raw": reg_raw,
                "reg_normalized": reg_normalized,
                "marks_raw": marks_raw,
                "absent_raw": absent_raw,
            })

        if not raw_rows:
            raise ValidationFailedException("CSV file contains header row but zero student data rows")

        # 10. Query institutional students and enrolled students directly
        all_student_reg_nos: Set[str] = set(
            db.execute(select(Student.registration_number)).scalars().all()
        )

        enrolled_student_reg_nos: Set[str] = set(
            db.execute(
                select(Student.registration_number)
                .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
                .where(
                    CourseEnrollment.course_id == course_id,
                    CourseEnrollment.session_id == session_id,
                    CourseEnrollment.is_active == True,
                )
            ).scalars().all()
        )

        # 11. Row-by-Row Deep Validation
        staged_rows_data = []
        total_errors = 0
        total_valid = 0
        sample_errors_summary = []

        for item in raw_rows:
            row_errors: List[Dict[str, Any]] = []
            row_num = item["row_number"]
            reg = item["reg_normalized"]
            marks_str = item["marks_raw"]
            absent_str = item["absent_raw"]

            # Registration number checks
            if not reg:
                row_errors.append({
                    "field": "registration_number",
                    "code": "MISSING_REGISTRATION_NUMBER",
                    "message": "Student registration number is required",
                })
            else:
                # In-file duplicate check
                if len(reg_counts.get(reg, [])) > 1:
                    duplicate_rows = ", ".join(str(r) for r in reg_counts[reg])
                    row_errors.append({
                        "field": "registration_number",
                        "code": "DUPLICATE_IN_FILE",
                        "message": f"Registration number '{reg}' appears multiple times (rows {duplicate_rows})",
                    })

                # Check student exists in university database
                if reg not in all_student_reg_nos:
                    row_errors.append({
                        "field": "registration_number",
                        "code": "STUDENT_NOT_FOUND",
                        "message": f"Registration number '{reg}' does not exist in student records",
                    })
                # Check student is enrolled in this course for this session
                elif reg not in enrolled_student_reg_nos:
                    row_errors.append({
                        "field": "registration_number",
                        "code": "NOT_ENROLLED",
                        "message": f"Student '{reg}' is not enrolled in this course for this session",
                    })

            # Absentee check
            is_absent_normalized = absent_str.lower() in ["yes", "true", "ab", "absent", "y", "1"]
            if marks_str.strip().upper() in ["AB", "ABSENT"]:
                is_absent_normalized = True
                marks_str = "0"

            # Marks checks
            if is_absent_normalized:
                if marks_str and marks_str not in ["0", "0.0", ""]:
                    try:
                        val = float(marks_str)
                        if val > 0:
                            row_errors.append({
                                "field": "marks_obtained",
                                "code": "ABSENT_WITH_MARKS",
                                "message": f"Student is marked absent, but non-zero marks ({marks_str}) were provided",
                            })
                    except ValueError:
                        row_errors.append({
                            "field": "marks_obtained",
                            "code": "INVALID_NUMERIC",
                            "message": f"Invalid marks entry '{marks_str}' for absent student",
                        })
            else:
                if not marks_str:
                    row_errors.append({
                        "field": "marks_obtained",
                        "code": "MARKS_REQUIRED",
                        "message": "Marks obtained cannot be blank for a present student",
                    })
                else:
                    try:
                        mark_val = float(marks_str)
                        if mark_val < 0:
                            row_errors.append({
                                "field": "marks_obtained",
                                "code": "NEGATIVE_MARKS",
                                "message": f"Marks cannot be negative (provided: {mark_val})",
                            })
                        elif mark_val > max_marks:
                            row_errors.append({
                                "field": "marks_obtained",
                                "code": "EXCEEDS_MAX_MARKS",
                                "message": f"Mark {mark_val} exceeds declared maximum marks of {max_marks}",
                            })
                    except ValueError:
                        row_errors.append({
                            "field": "marks_obtained",
                            "code": "INVALID_NUMERIC",
                            "message": f"Marks '{marks_str}' must be a valid numeric value",
                        })

            is_row_valid = len(row_errors) == 0
            if is_row_valid:
                total_valid += 1
            else:
                total_errors += 1
                if len(sample_errors_summary) < 20:
                    sample_errors_summary.append({
                        "row_number": row_num,
                        "registration_number": item["reg_raw"],
                        "errors": row_errors,
                    })

            staged_rows_data.append({
                "row_number": row_num,
                "raw_registration_number": item["reg_raw"],
                "raw_marks_obtained": item["marks_raw"],
                "is_absent": is_absent_normalized,
                "is_valid": is_row_valid,
                "validation_errors": row_errors if row_errors else None,
            })

        # 12. Create Batch Record with Staged Rows
        batch_status = BatchStatus.PENDING_APPROVAL if total_errors == 0 else BatchStatus.VALIDATION_FAILED

        batch = MarkImportBatch(
            session_id=session_id,
            course_id=course_id,
            uploaded_by_teacher_id=teacher_id,
            max_marks=max_marks,
            file_name=file_name,
            file_hash=file_hash,
            total_rows=len(raw_rows),
            valid_rows=total_valid,
            error_rows=total_errors,
            status=batch_status,
        )
        db.add(batch)
        db.flush()

        for row_dict in staged_rows_data:
            db_row = MarkImportRow(
                batch_id=batch.id,
                row_number=row_dict["row_number"],
                raw_registration_number=row_dict["raw_registration_number"],
                raw_marks_obtained=row_dict["raw_marks_obtained"],
                is_absent=row_dict["is_absent"],
                is_valid=row_dict["is_valid"],
                validation_errors=row_dict["validation_errors"],
            )
            db.add(db_row)

        db.commit()
        db.refresh(batch)

        return batch, sample_errors_summary
