import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.marks.models import OfficialMark
from app.modules.marks.schemas import OfficialMarkOut
from app.modules.users_mgmt.models import Student
from app.modules.academic.models import Course
from app.core.exceptions import NotFoundException


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
