import uuid
from typing import List, Optional, Tuple, Dict, Any
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User
from app.modules.users_mgmt.models import Teacher, Student
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.marks.models import OfficialMark
from app.modules.audit.models import AuditLog
from app.modules.imports.schemas import (
    TemplateInfoOut, TemplateColumnInfo, BatchOut, BatchDetailOut, BatchRowOut
)
from app.modules.imports.validator import CSVValidationEngine
from app.core.enums import UserRole, BatchStatus
from app.core.models_base import utcnow
from app.core.exceptions import (
    NotFoundException, ForbiddenException, ConflictException, ValidationFailedException
)


class ImportsService:
    """Service orchestrating mark file validation, staging, and import history."""

    @staticmethod
    def get_template_info() -> TemplateInfoOut:
        """Return the standard CSV structure and sample format for faculty mark entry."""
        columns = [
            TemplateColumnInfo(
                name="registration_number",
                required=True,
                description="Unique university student registration number.",
                example="REG2026001",
            ),
            TemplateColumnInfo(
                name="student_name",
                required=False,
                description="Student name (optional; verified against database records).",
                example="John Doe",
            ),
            TemplateColumnInfo(
                name="marks_obtained",
                required=True,
                description="Marks obtained (0 up to declared max_marks). Leave blank or 0 if student was absent.",
                example="42.5",
            ),
            TemplateColumnInfo(
                name="is_absent",
                required=True,
                description="Mark 'YES' or 'AB' if absent, or 'NO' if present.",
                example="NO",
            ),
            TemplateColumnInfo(
                name="remarks",
                required=False,
                description="Optional explanatory note.",
                example="Regular examination",
            ),
        ]
        sample_csv = (
            "registration_number,student_name,marks_obtained,is_absent,remarks\n"
            "REG2026001,John Doe,42.5,NO,\n"
            "REG2026002,Jane Smith,,,YES,Medical absence\n"
            "REG2026003,Bob Johnson,38.0,NO,\n"
        )
        return TemplateInfoOut(columns=columns, csv_sample=sample_csv)

    @staticmethod
    def upload_marks_csv(
        db: Session,
        teacher_user: User,
        session_id: uuid.UUID,
        course_id: uuid.UUID,
        max_marks: float,
        file: UploadFile,
    ) -> Tuple[BatchDetailOut, List[Dict[str, Any]]]:
        """Validate uploaded marks CSV file and stage in mark_import_batches."""
        # Find teacher profile
        teacher = db.execute(
            select(Teacher).where(Teacher.user_id == teacher_user.id)
        ).scalar_one_or_none()

        if not teacher:
            raise ForbiddenException("Only registered faculty members can upload student marks")

        file_bytes = file.file.read()
        file_name = file.filename or "marks.csv"

        batch, sample_errors = CSVValidationEngine.validate_and_stage_csv(
            db=db,
            session_id=session_id,
            course_id=course_id,
            teacher_id=teacher.id,
            max_marks=max_marks,
            file_name=file_name,
            file_bytes=file_bytes,
        )

        detail = BatchDetailOut(
            id=batch.id,
            session_id=batch.session_id,
            course_id=batch.course_id,
            uploaded_by_teacher_id=batch.uploaded_by_teacher_id,
            max_marks=batch.max_marks,
            file_name=batch.file_name,
            file_hash=batch.file_hash,
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            error_rows=batch.error_rows,
            status=batch.status,
            rejection_reason=batch.rejection_reason,
            reviewed_by_admin_id=batch.reviewed_by_admin_id,
            reviewed_at=batch.reviewed_at,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            sample_errors=sample_errors,
        )
        return detail, sample_errors

    @staticmethod
    def get_batch(db: Session, batch_id: uuid.UUID, current_user: User) -> BatchDetailOut:
        batch = db.execute(
            select(MarkImportBatch)
            .options(
                joinedload(MarkImportBatch.session),
                joinedload(MarkImportBatch.teacher).joinedload(Teacher.user),
            )
            .where(MarkImportBatch.id == batch_id)
        ).scalar_one_or_none()

        if not batch:
            raise NotFoundException(f"Import batch with ID {batch_id} not found")

        # Teachers can only view their own uploaded batches
        if current_user.role == UserRole.TEACHER:
            teacher = db.execute(select(Teacher).where(Teacher.user_id == current_user.id)).scalar_one_or_none()
            if not teacher or batch.uploaded_by_teacher_id != teacher.id:
                raise ForbiddenException("You do not have permission to view this upload batch")

        # Get course code and name
        from app.modules.academic.models import Course
        course = db.get(Course, batch.course_id)

        # Get sample errors if any
        error_rows = db.execute(
            select(MarkImportRow)
            .where(MarkImportRow.batch_id == batch_id, MarkImportRow.is_valid == False)
            .limit(20)
        ).scalars().all()

        sample_errors = [
            {
                "row_number": r.row_number,
                "registration_number": r.raw_registration_number,
                "errors": r.validation_errors,
            }
            for r in error_rows
        ]

        return BatchDetailOut(
            id=batch.id,
            session_id=batch.session_id,
            course_id=batch.course_id,
            uploaded_by_teacher_id=batch.uploaded_by_teacher_id,
            max_marks=batch.max_marks,
            file_name=batch.file_name,
            file_hash=batch.file_hash,
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            error_rows=batch.error_rows,
            status=batch.status,
            rejection_reason=batch.rejection_reason,
            reviewed_by_admin_id=batch.reviewed_by_admin_id,
            reviewed_at=batch.reviewed_at,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            session_name=batch.session.name if batch.session else None,
            course_code=course.code if course else None,
            course_name=course.name if course else None,
            teacher_name=batch.teacher.user.full_name if batch.teacher else None,
            sample_errors=sample_errors,
        )

    @staticmethod
    def list_batches(
        db: Session,
        current_user: User,
        session_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
    ) -> List[BatchOut]:
        query = select(MarkImportBatch)

        # Restrict teacher to own uploads
        if current_user.role == UserRole.TEACHER:
            teacher = db.execute(select(Teacher).where(Teacher.user_id == current_user.id)).scalar_one_or_none()
            if not teacher:
                return []
            query = query.where(MarkImportBatch.uploaded_by_teacher_id == teacher.id)

        if session_id:
            query = query.where(MarkImportBatch.session_id == session_id)
        if course_id:
            query = query.where(MarkImportBatch.course_id == course_id)

        batches = db.execute(query.order_by(MarkImportBatch.created_at.desc())).scalars().all()
        return [BatchOut.model_validate(b) for b in batches]

    @staticmethod
    def get_batch_rows(
        db: Session,
        batch_id: uuid.UUID,
        current_user: User,
        errors_only: bool = False,
    ) -> List[BatchRowOut]:
        # Validate access to batch
        ImportsService.get_batch(db, batch_id, current_user)

        query = select(MarkImportRow).where(MarkImportRow.batch_id == batch_id)
        if errors_only:
            query = query.where(MarkImportRow.is_valid == False)

        rows = db.execute(query.order_by(MarkImportRow.row_number)).scalars().all()
        return [BatchRowOut.model_validate(r) for r in rows]

    @staticmethod
    def approve_batch(db: Session, batch_id: uuid.UUID, admin_user: User) -> BatchDetailOut:
        """
        Transactional administrative approval:
        - Transfers staged rows from mark_import_rows to official_marks.
        - Updates batch status to IMPORTED.
        - Creates immutable audit record.
        """
        query = select(MarkImportBatch).where(MarkImportBatch.id == batch_id)
        if db.bind and db.bind.dialect.name == "postgresql":
            query = query.with_for_update()
        batch = db.execute(query).scalar_one_or_none()
        if not batch:
            raise NotFoundException(f"Import batch with ID {batch_id} not found")

        if batch.status == BatchStatus.IMPORTED:
            raise ConflictException("This batch has already been approved and imported into official records")

        if batch.status == BatchStatus.VALIDATION_FAILED:
            raise ValidationFailedException(
                "Cannot approve a batch with validation errors. The faculty member must correct and re-upload the file."
            )

        if batch.status != BatchStatus.PENDING_APPROVAL:
            raise ConflictException(f"Cannot approve batch in '{batch.status.value}' status")

        # Check existing official marks
        existing = db.execute(
            select(OfficialMark).where(
                OfficialMark.session_id == batch.session_id,
                OfficialMark.course_id == batch.course_id,
            )
        ).first()
        if existing:
            raise ConflictException("Official marks already exist for this course in this session")

        # Staged rows
        staged_rows = db.execute(
            select(MarkImportRow).where(MarkImportRow.batch_id == batch.id, MarkImportRow.is_valid == True)
        ).scalars().all()

        needed_regs = [r.raw_registration_number.strip().upper() for r in staged_rows if r.raw_registration_number]
        students_by_reg = {
            s.registration_number: s
            for s in db.execute(
                select(Student).where(Student.registration_number.in_(needed_regs))
            ).scalars().all()
        } if needed_regs else {}

        for row in staged_rows:
            student = students_by_reg.get(row.raw_registration_number.strip().upper())
            if not student:
                raise ValidationFailedException(
                    f"Student with registration number '{row.raw_registration_number}' not found during import"
                )

            marks_val = 0.0
            if not row.is_absent and row.raw_marks_obtained:
                marks_val = float(row.raw_marks_obtained)

            official_mark = OfficialMark(
                session_id=batch.session_id,
                course_id=batch.course_id,
                student_id=student.id,
                batch_id=batch.id,
                marks_obtained=marks_val,
                max_marks=batch.max_marks,
                is_absent=row.is_absent,
                is_amended=False,
            )
            db.add(official_mark)

        # Update batch status
        batch.status = BatchStatus.IMPORTED
        batch.reviewed_by_admin_id = admin_user.id
        batch.reviewed_at = utcnow()

        # Audit log
        audit_entry = AuditLog(
            user_id=admin_user.id,
            action="IMPORT_BATCH_APPROVED",
            entity_type="mark_import_batches",
            entity_id=str(batch.id),
            details={
                "session_id": str(batch.session_id),
                "course_id": str(batch.course_id),
                "total_official_marks_imported": len(staged_rows),
                "max_marks": batch.max_marks,
            },
        )
        db.add(audit_entry)

        db.commit()
        db.refresh(batch)
        return ImportsService.get_batch(db, batch.id, admin_user)

    @staticmethod
    def reject_batch(db: Session, batch_id: uuid.UUID, reason: str, admin_user: User) -> BatchDetailOut:
        """
        Administrative rejection:
        - Marks batch as REJECTED with mandatory reason.
        - Staged rows remain for review but never become official marks.
        - Creates audit record.
        """
        batch = db.get(MarkImportBatch, batch_id)
        if not batch:
            raise NotFoundException(f"Import batch with ID {batch_id} not found")

        if batch.status == BatchStatus.IMPORTED:
            raise ConflictException("Cannot reject a batch that has already been imported into official records")

        batch.status = BatchStatus.REJECTED
        batch.rejection_reason = reason.strip()
        batch.reviewed_by_admin_id = admin_user.id
        batch.reviewed_at = utcnow()

        audit_entry = AuditLog(
            user_id=admin_user.id,
            action="IMPORT_BATCH_REJECTED",
            entity_type="mark_import_batches",
            entity_id=str(batch.id),
            details={
                "reason": reason.strip(),
                "session_id": str(batch.session_id),
                "course_id": str(batch.course_id),
            },
        )
        db.add(audit_entry)

        db.commit()
        db.refresh(batch)
        return ImportsService.get_batch(db, batch.id, admin_user)

