import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.core.enums import SessionStatus, ResultStatus
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from app.core.models_base import utcnow
from app.modules.academic.models import ExaminationSession, Course
from app.modules.users_mgmt.models import CourseEnrollment, Student
from app.modules.marks.models import OfficialMark
from app.modules.results.models import CalculatedResult, ResultSubjectDetail
from app.modules.results.schemas import (
    CalculatedResultOut,
    ResultSubjectDetailOut,
    CalculationSummaryOut,
    StudentMarksheetOut,
    StudentSubjectResultOut,
)
from app.modules.audit.service import AuditService


class ResultsService:
    """Academic calculation engine and result management service."""

    @staticmethod
    def calculate_session_results(
        db: Session,
        session_id: uuid.UUID,
        current_user_id: uuid.UUID,
        allow_partial: bool = False,
    ) -> CalculationSummaryOut:
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")

        if session.status == SessionStatus.ARCHIVED:
            raise ConflictException("Cannot calculate results for an archived examination session")
        if session.status == SessionStatus.PUBLISHED:
            raise ConflictException(
                "Results have already been published. Recalculation requires specific administrative rollback or amendment."
            )

        # 1. Fetch all course enrollments for this session
        enrollments = db.execute(
            select(CourseEnrollment)
            .options(
                joinedload(CourseEnrollment.student).joinedload(Student.user),
                joinedload(CourseEnrollment.student).joinedload(Student.program),
                joinedload(CourseEnrollment.course),
            )
            .where(CourseEnrollment.session_id == session_id)
        ).scalars().all()

        if not enrollments:
            raise ValidationException("No student course enrollments found for this examination session")

        # 2. Fetch all official approved marks for this session
        official_marks = db.execute(
            select(OfficialMark).where(OfficialMark.session_id == session_id)
        ).scalars().all()

        mark_map = {(m.student_id, m.course_id): m for m in official_marks}

        # 3. Check for missing marks
        missing = [e for e in enrollments if (e.student_id, e.course_id) not in mark_map]
        if missing and not allow_partial:
            missing_course_codes = sorted(set(e.course.code for e in missing))
            raise ValidationException(
                f"Cannot calculate results: {len(missing)} student enrollment(s) lack official approved marks "
                f"across courses: {', '.join(missing_course_codes)}. "
                "Ensure all batches are approved, or set allow_partial=True."
            )

        # 4. Update session status to CALCULATING
        session.status = SessionStatus.CALCULATING
        db.flush()

        # 5. Clear existing results for idempotence
        existing_results = db.execute(
            select(CalculatedResult).where(CalculatedResult.session_id == session_id)
        ).scalars().all()
        for er in existing_results:
            db.delete(er)
        db.flush()

        # 6. Group enrollments by student
        student_enrollments: dict[uuid.UUID, list[CourseEnrollment]] = {}
        for e in enrollments:
            student_enrollments.setdefault(e.student_id, []).append(e)

        # 7. Evaluate each student's results
        for student_id, s_enrollments in student_enrollments.items():
            total_obtained = 0.0
            total_max = 0.0
            has_failed_subject = False
            subject_details: list[ResultSubjectDetail] = []

            for enrollment in s_enrollments:
                course = enrollment.course
                mark = mark_map.get((enrollment.student_id, enrollment.course_id))

                if not mark:
                    # Missing mark during partial calculation
                    marks_obtained = 0.0
                    max_marks = 100.0
                    is_absent = True
                    is_passed = False
                    pct = 0.0
                    remarks = "NO_MARKS"
                    has_failed_subject = True
                else:
                    marks_obtained = mark.marks_obtained
                    max_marks = mark.max_marks
                    is_absent = mark.is_absent
                    pct = round((marks_obtained / max_marks * 100), 2) if max_marks > 0 else 0.0
                    is_passed = (not is_absent) and (pct >= course.pass_percentage)
                    remarks = "ABSENT" if is_absent else ("PASS" if is_passed else "FAIL")
                    if not is_passed:
                        has_failed_subject = True

                total_obtained += marks_obtained
                total_max += max_marks

                subject_detail = ResultSubjectDetail(
                    course_id=course.id,
                    marks_obtained=round(marks_obtained, 2),
                    max_marks=round(max_marks, 2),
                    percentage=pct,
                    is_absent=is_absent,
                    is_passed=is_passed,
                    remarks=remarks,
                )
                subject_details.append(subject_detail)

            overall_percentage = round((total_obtained / total_max * 100), 2) if total_max > 0 else 0.0
            overall_status = ResultStatus.FAIL if has_failed_subject else ResultStatus.PASS

            calculated_result = CalculatedResult(
                session_id=session_id,
                student_id=student_id,
                total_marks_obtained=round(total_obtained, 2),
                total_max_marks=round(total_max, 2),
                percentage=overall_percentage,
                result_status=overall_status,
                is_withheld=False,
                calculated_at=utcnow(),
                subject_details=subject_details,
            )
            db.add(calculated_result)

        # 8. Mark session as CALCULATED
        session.status = SessionStatus.CALCULATED

        # 9. Audit trail
        AuditService.log(
            db=db,
            user_id=current_user_id,
            action="CALCULATE_RESULTS",
            entity_type="examination_sessions",
            entity_id=str(session.id),
            details={
                "session_name": session.name,
                "total_evaluated": len(student_enrollments),
            },
        )

        db.commit()
        return ResultsService.get_session_summary(db, session_id)

    @staticmethod
    def get_session_summary(db: Session, session_id: uuid.UUID) -> CalculationSummaryOut:
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")

        # Distinct enrolled students count
        total_enrolled = db.execute(
            select(func.count(func.distinct(CourseEnrollment.student_id))).where(
                CourseEnrollment.session_id == session_id
            )
        ).scalar() or 0

        results = db.execute(
            select(CalculatedResult).where(CalculatedResult.session_id == session_id)
        ).scalars().all()

        total_evaluated = len(results)
        total_passed = sum(1 for r in results if r.result_status == ResultStatus.PASS)
        total_failed = sum(1 for r in results if r.result_status == ResultStatus.FAIL)
        total_withheld = sum(1 for r in results if r.is_withheld)

        percentages = [r.percentage for r in results]
        pass_pct = round((total_passed / total_evaluated * 100), 2) if total_evaluated > 0 else 0.0
        avg_pct = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
        highest_pct = max(percentages) if percentages else 0.0
        lowest_pct = min(percentages) if percentages else 0.0

        return CalculationSummaryOut(
            session_id=session.id,
            session_name=session.name,
            academic_year=session.academic_year,
            semester_number=session.semester_number,
            status=session.status.value,
            total_students_enrolled=total_enrolled,
            total_students_evaluated=total_evaluated,
            total_passed=total_passed,
            total_failed=total_failed,
            total_withheld=total_withheld,
            overall_pass_percentage=pass_pct,
            average_percentage=avg_pct,
            highest_percentage=highest_pct,
            lowest_percentage=lowest_pct,
        )

    @staticmethod
    def list_session_results(
        db: Session,
        session_id: uuid.UUID,
        result_status: Optional[ResultStatus] = None,
        is_withheld: Optional[bool] = None,
    ) -> List[CalculatedResultOut]:
        query = (
            select(CalculatedResult)
            .options(
                joinedload(CalculatedResult.student).joinedload(Student.user),
                joinedload(CalculatedResult.student).joinedload(Student.program),
                joinedload(CalculatedResult.subject_details).joinedload(ResultSubjectDetail.course),
            )
            .where(CalculatedResult.session_id == session_id)
        )

        if result_status:
            query = query.where(CalculatedResult.result_status == result_status)
        if is_withheld is not None:
            query = query.where(CalculatedResult.is_withheld == is_withheld)

        results = db.execute(query).unique().scalars().all()

        return [
            CalculatedResultOut(
                id=r.id,
                session_id=r.session_id,
                student_id=r.student_id,
                registration_number=r.student.registration_number if r.student else None,
                student_name=r.student.user.full_name if r.student and r.student.user else None,
                program_code=r.student.program.code if r.student and r.student.program else None,
                program_name=r.student.program.name if r.student and r.student.program else None,
                total_marks_obtained=r.total_marks_obtained,
                total_max_marks=r.total_max_marks,
                percentage=r.percentage,
                result_status=r.result_status,
                is_withheld=r.is_withheld,
                calculated_at=r.calculated_at,
                subject_details=[
                    ResultSubjectDetailOut(
                        id=sd.id,
                        course_id=sd.course_id,
                        course_code=sd.course.code,
                        course_name=sd.course.name,
                        credits=sd.course.credits,
                        marks_obtained=sd.marks_obtained,
                        max_marks=sd.max_marks,
                        percentage=sd.percentage,
                        is_absent=sd.is_absent,
                        is_passed=sd.is_passed,
                        remarks=sd.remarks,
                    )
                    for sd in r.subject_details
                ],
            )
            for r in results
        ]

    @staticmethod
    def get_student_result(
        db: Session,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> CalculatedResultOut:
        result = db.execute(
            select(CalculatedResult)
            .options(
                joinedload(CalculatedResult.student).joinedload(Student.user),
                joinedload(CalculatedResult.student).joinedload(Student.program),
                joinedload(CalculatedResult.subject_details).joinedload(ResultSubjectDetail.course),
            )
            .where(
                CalculatedResult.session_id == session_id,
                CalculatedResult.student_id == student_id,
            )
        ).unique().scalar_one_or_none()

        if not result:
            raise NotFoundException(f"Calculated result not found for student in session {session_id}")

        return CalculatedResultOut(
            id=result.id,
            session_id=result.session_id,
            student_id=result.student_id,
            registration_number=result.student.registration_number if result.student else None,
            student_name=result.student.user.full_name if result.student and result.student.user else None,
            program_code=result.student.program.code if result.student and result.student.program else None,
            program_name=result.student.program.name if result.student and result.student.program else None,
            total_marks_obtained=result.total_marks_obtained,
            total_max_marks=result.total_max_marks,
            percentage=result.percentage,
            result_status=result.result_status,
            is_withheld=result.is_withheld,
            calculated_at=result.calculated_at,
            subject_details=[
                ResultSubjectDetailOut(
                    id=sd.id,
                    course_id=sd.course_id,
                    course_code=sd.course.code,
                    course_name=sd.course.name,
                    credits=sd.course.credits,
                    marks_obtained=sd.marks_obtained,
                    max_marks=sd.max_marks,
                    percentage=sd.percentage,
                    is_absent=sd.is_absent,
                    is_passed=sd.is_passed,
                    remarks=sd.remarks,
                )
                for sd in result.subject_details
            ],
        )

    @staticmethod
    def set_withheld_status(
        db: Session,
        result_id: uuid.UUID,
        is_withheld: bool,
        reason: Optional[str],
        current_user_id: uuid.UUID,
    ) -> CalculatedResultOut:
        result = db.get(CalculatedResult, result_id)
        if not result:
            raise NotFoundException(f"Calculated result with ID {result_id} not found")

        result.is_withheld = is_withheld

        AuditService.log(
            db=db,
            user_id=current_user_id,
            action="WITHHOLD_RESULT" if is_withheld else "RELEASE_RESULT",
            entity_type="calculated_results",
            entity_id=str(result.id),
            details={
                "student_id": str(result.student_id),
                "is_withheld": is_withheld,
                "reason": reason,
            },
        )
        db.commit()

        return ResultsService.get_student_result(db, result.session_id, result.student_id)

    @staticmethod
    def publish_session_results(
        db: Session,
        session_id: uuid.UUID,
        admin_user_id: uuid.UUID,
    ) -> CalculationSummaryOut:
        """Officially publish calculated results for an examination session (Admin only)."""
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")

        if session.status != SessionStatus.CALCULATED:
            raise ConflictException(
                f"Cannot publish examination session in status '{session.status.value}'. "
                "Results must be in 'CALCULATED' status before publishing."
            )

        session.status = SessionStatus.PUBLISHED
        session.published_at = utcnow()
        session.published_by_user_id = admin_user_id

        AuditService.log(
            db=db,
            user_id=admin_user_id,
            action="PUBLISH_SESSION_RESULTS",
            entity_type="examination_sessions",
            entity_id=str(session.id),
            details={
                "session_name": session.name,
                "published_at": session.published_at.isoformat(),
            },
        )
        db.commit()

        return ResultsService.get_session_summary(db, session_id)

    @staticmethod
    def unpublish_session_results(
        db: Session,
        session_id: uuid.UUID,
        reason: str,
        admin_user_id: uuid.UUID,
    ) -> CalculationSummaryOut:
        """Rollback published status to CALCULATED for emergency administrative corrections."""
        session = db.get(ExaminationSession, session_id)
        if not session:
            raise NotFoundException(f"Examination session with ID {session_id} not found")

        if session.status != SessionStatus.PUBLISHED:
            raise ConflictException("Only currently PUBLISHED examination sessions can be unpublished.")

        session.status = SessionStatus.CALCULATED
        session.published_at = None
        session.published_by_user_id = None

        AuditService.log(
            db=db,
            user_id=admin_user_id,
            action="UNPUBLISH_SESSION_RESULTS",
            entity_type="examination_sessions",
            entity_id=str(session.id),
            details={
                "session_name": session.name,
                "reason": reason,
            },
        )
        db.commit()

        return ResultsService.get_session_summary(db, session_id)

    @staticmethod
    def get_student_marksheets(
        db: Session,
        student_user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> List[StudentMarksheetOut]:
        """Fetch official published results for the authenticated student."""
        student = db.execute(
            select(Student)
            .options(joinedload(Student.user), joinedload(Student.program))
            .where(Student.user_id == student_user_id)
        ).scalar_one_or_none()

        if not student:
            raise NotFoundException("Student profile not found for authenticated user")

        query = (
            select(CalculatedResult)
            .join(ExaminationSession, CalculatedResult.session_id == ExaminationSession.id)
            .options(
                joinedload(CalculatedResult.session),
                joinedload(CalculatedResult.subject_details).joinedload(ResultSubjectDetail.course),
            )
            .where(
                CalculatedResult.student_id == student.id,
                ExaminationSession.status == SessionStatus.PUBLISHED,
            )
        )

        if session_id:
            query = query.where(CalculatedResult.session_id == session_id)

        results = db.execute(query).unique().scalars().all()

        marksheets: List[StudentMarksheetOut] = []
        for r in results:
            if r.is_withheld:
                marksheets.append(
                    StudentMarksheetOut(
                        session_id=r.session_id,
                        session_name=r.session.name,
                        academic_year=r.session.academic_year,
                        semester_number=r.session.semester_number,
                        published_at=r.session.published_at,
                        student_name=student.user.full_name,
                        registration_number=student.registration_number,
                        program_code=student.program.code,
                        program_name=student.program.name,
                        is_withheld=True,
                        total_marks_obtained=None,
                        total_max_marks=None,
                        percentage=None,
                        result_status=None,
                        notice="Your official result for this examination session has been withheld. Please contact the university examination branch.",
                        subjects=[],
                    )
                )
            else:
                subjects = [
                    StudentSubjectResultOut(
                        course_code=sd.course.code,
                        course_name=sd.course.name,
                        credits=sd.course.credits,
                        marks_obtained=sd.marks_obtained,
                        max_marks=sd.max_marks,
                        percentage=sd.percentage,
                        is_absent=sd.is_absent,
                        is_passed=sd.is_passed,
                        remarks=sd.remarks,
                    )
                    for sd in r.subject_details
                ]
                marksheets.append(
                    StudentMarksheetOut(
                        session_id=r.session_id,
                        session_name=r.session.name,
                        academic_year=r.session.academic_year,
                        semester_number=r.session.semester_number,
                        published_at=r.session.published_at,
                        student_name=student.user.full_name,
                        registration_number=student.registration_number,
                        program_code=student.program.code,
                        program_name=student.program.name,
                        is_withheld=False,
                        total_marks_obtained=r.total_marks_obtained,
                        total_max_marks=r.total_max_marks,
                        percentage=r.percentage,
                        result_status=r.result_status,
                        notice=None,
                        subjects=subjects,
                    )
                )

        return marksheets

