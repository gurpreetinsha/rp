import uuid
from typing import List, Optional, Tuple, Dict, Any
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User
from app.modules.users_mgmt.models import Teacher
from app.modules.imports.models import MarkImportBatch, MarkImportRow
from app.modules.imports.schemas import (
    TemplateInfoOut, TemplateColumnInfo, BatchOut, BatchDetailOut, BatchRowOut
)
from app.modules.imports.validator import CSVValidationEngine
from app.core.enums import UserRole
from app.core.exceptions import NotFoundException, ForbiddenException


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
