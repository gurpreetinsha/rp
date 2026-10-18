import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.marks.models import OfficialMark, MarkAmendment
from app.modules.marks.schemas import OfficialMarkOut, MarkAmendmentOut, AmendMarkRequest
from app.modules.users_mgmt.models import Student, CourseEnrollment
from app.modules.academic.models import Course, ExaminationSession
from app.modules.results.models import CalculatedResult, ResultSubjectDetail
from app.modules.audit.service import AuditService
from app.core.models_base import utcnow
from app.core.enums import SessionStatus, ResultStatus
from app.core.exceptions import NotFoundException, ValidationException


class MarksService:
    """Service handling official academic mark queries."""

    @staticmethod
    def list_official_marks(
        db: Session,
        session_id: uuid.UUID,
        course_id: Optional[uuid.UUID] = None,
        student_id: Optional[uuid.UUID] = None,
    ) -> List[OfficialMarkOut]:
        query = (
            select(OfficialMark)
            .options(
                joinedload(OfficialMark.student).joinedload(Student.user),
                joinedload(OfficialMark.course),
            )
            .where(OfficialMark.session_id == session_id)
        )

        if course_id:
            query = query.where(OfficialMark.course_id == course_id)
        if student_id:
            query = query.where(OfficialMark.student_id == student_id)

        marks = db.execute(query).scalars().all()
        return [
            OfficialMarkOut(
                id=m.id,
                session_id=m.session_id,
                course_id=m.course_id,
                student_id=m.student_id,
                batch_id=m.batch_id,
                marks_obtained=m.marks_obtained,
                max_marks=m.max_marks,
                percentage=round((m.marks_obtained / m.max_marks * 100), 2) if m.max_marks > 0 else 0.0,
                is_absent=m.is_absent,
                is_amended=m.is_amended,
                registration_number=m.student.registration_number if m.student else None,
                student_name=m.student.user.full_name if m.student and m.student.user else None,
                course_code=m.course.code if m.course else None,
                course_name=m.course.name if m.course else None,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in marks
        ]

    @staticmethod
    def get_official_mark(db: Session, mark_id: uuid.UUID) -> OfficialMarkOut:
        m = db.execute(
            select(OfficialMark)
            .options(
                joinedload(OfficialMark.student).joinedload(Student.user),
                joinedload(OfficialMark.course),
            )
            .where(OfficialMark.id == mark_id)
        ).scalar_one_or_none()

        if not m:
            raise NotFoundException(f"Official mark with ID {mark_id} not found")

        return OfficialMarkOut(
            id=m.id,
            session_id=m.session_id,
            course_id=m.course_id,
            student_id=m.student_id,
            batch_id=m.batch_id,
            marks_obtained=m.marks_obtained,
            max_marks=m.max_marks,
            percentage=round((m.marks_obtained / m.max_marks * 100), 2) if m.max_marks > 0 else 0.0,
            is_absent=m.is_absent,
            is_amended=m.is_amended,
            registration_number=m.student.registration_number if m.student else None,
            student_name=m.student.user.full_name if m.student and m.student.user else None,
            course_code=m.course.code if m.course else None,
            course_name=m.course.name if m.course else None,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    @staticmethod
    def amend_official_mark(
        db: Session,
        mark_id: uuid.UUID,
        payload: AmendMarkRequest,
        admin_user_id: uuid.UUID,
    ) -> OfficialMarkOut:
        """Formally amend an official mark with full audit trail and result recalculation."""
        m = db.get(OfficialMark, mark_id)
        if not m:
            raise NotFoundException(f"Official mark with ID {mark_id} not found")

        # Validation
        if payload.new_is_absent:
            final_marks = 0.0
        else:
            if payload.new_marks_obtained < 0 or payload.new_marks_obtained > m.max_marks:
                raise ValidationException(
                    f"Amended marks ({payload.new_marks_obtained}) must be between 0 and maximum marks ({m.max_marks})"
                )
            final_marks = round(payload.new_marks_obtained, 2)

        old_marks = m.marks_obtained
        old_absent = m.is_absent

        # Update official mark
        m.marks_obtained = final_marks
        m.is_absent = payload.new_is_absent
        m.is_amended = True

        # Insert amendment record
        amendment = MarkAmendment(
            official_mark_id=m.id,
            old_marks_obtained=old_marks,
            new_marks_obtained=final_marks,
            old_is_absent=old_absent,
            new_is_absent=payload.new_is_absent,
            reason=payload.reason,
            requested_by_id=payload.requested_by_id or admin_user_id,
            approved_by_id=admin_user_id,
            amended_at=utcnow(),
        )
        db.add(amendment)

        # Audit log
        AuditService.log(
            db=db,
            user_id=admin_user_id,
            action="AMEND_OFFICIAL_MARK",
            entity_type="official_marks",
            entity_id=str(m.id),
            details={
                "old_marks": old_marks,
                "new_marks": final_marks,
                "old_is_absent": old_absent,
                "new_is_absent": payload.new_is_absent,
                "reason": payload.reason,
            },
        )

        # Auto-recalculate student's calculated result if session is CALCULATED or PUBLISHED
        session = db.get(ExaminationSession, m.session_id)
        if session and session.status in [SessionStatus.CALCULATED, SessionStatus.PUBLISHED]:
            student_calc = db.execute(
                select(CalculatedResult)
                .options(joinedload(CalculatedResult.subject_details).joinedload(ResultSubjectDetail.course))
                .where(
                    CalculatedResult.session_id == m.session_id,
                    CalculatedResult.student_id == m.student_id,
                )
            ).unique().scalar_one_or_none()

            if student_calc:
                # Update matching subject detail
                total_obtained = 0.0
                total_max = 0.0
                has_failed = False

                for sd in student_calc.subject_details:
                    if sd.course_id == m.course_id:
                        sd.marks_obtained = final_marks
                        sd.is_absent = payload.new_is_absent
                        sd.percentage = round((final_marks / sd.max_marks * 100), 2) if sd.max_marks > 0 else 0.0
                        sd.is_passed = (not sd.is_absent) and (sd.percentage >= sd.course.pass_percentage)
                        sd.remarks = "ABSENT" if sd.is_absent else ("PASS" if sd.is_passed else "FAIL")

                    total_obtained += sd.marks_obtained
                    total_max += sd.max_marks
                    if not sd.is_passed:
                        has_failed = True

                student_calc.total_marks_obtained = round(total_obtained, 2)
                student_calc.total_max_marks = round(total_max, 2)
                student_calc.percentage = round((total_obtained / total_max * 100), 2) if total_max > 0 else 0.0
                student_calc.result_status = ResultStatus.FAIL if has_failed else ResultStatus.PASS

        db.commit()
        return MarksService.get_official_mark(db, mark_id)

    @staticmethod
    def list_amendments(db: Session, mark_id: uuid.UUID) -> List[MarkAmendmentOut]:
        """List historical post-publication amendments for an official mark."""
        amendments = db.execute(
            select(MarkAmendment)
            .where(MarkAmendment.official_mark_id == mark_id)
            .order_by(MarkAmendment.amended_at.desc())
        ).scalars().all()

        return [MarkAmendmentOut.model_validate(a) for a in amendments]

