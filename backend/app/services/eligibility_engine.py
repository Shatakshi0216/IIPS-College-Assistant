"""
Personalized Notice & Student Eligibility Matching Engine
Evaluates whether a given notice matches a student's profile attributes
(branch, year, semester, CGPA) to filter feeds and trigger targeted push notifications.
"""
from typing import List
from sqlalchemy.orm import Session
from app.models.user import StudentProfile
from app.models.document import NoticeMetadata


def is_student_eligible(student: StudentProfile, notice: NoticeMetadata) -> bool:
    """
    Evaluates rule-based eligibility:
    1. Branch Match: Notice must be for 'ALL' or include student's branch.
    2. Year Match: Notice must be for all years or include student's current year.
    3. CGPA Match: Student's CGPA must meet or exceed minimum required CGPA.
    """
    if not notice:
        return True

    # 1. Branch Check
    if notice.eligible_branches:
        normalized_branches = [str(b).strip().upper() for b in notice.eligible_branches]
        if "ALL" not in normalized_branches and student.branch.strip().upper() not in normalized_branches:
            return False

    # 2. Year Check
    if notice.eligible_years:
        normalized_years = [str(y).strip().upper() for y in notice.eligible_years]
        if "ALL" not in normalized_years and str(student.year) not in normalized_years:
            return False

    # 3. CGPA Check
    if notice.min_cgpa and notice.min_cgpa > 0.0:
        if student.cgpa < notice.min_cgpa:
            return False

    return True


def filter_notices_for_student(student: StudentProfile, notices: List[NoticeMetadata]) -> List[NoticeMetadata]:
    """Filters a list of notices, returning only those relevant to the student."""
    return [notice for notice in notices if is_student_eligible(student, notice)]


def get_eligible_students(db: Session, notice: NoticeMetadata) -> List[StudentProfile]:
    """
    Finds all students eligible for a specific notice to send notifications to their devices.
    """
    query = db.query(StudentProfile)

    # Branch filter
    if notice.eligible_branches:
        branches = [str(b).strip().upper() for b in notice.eligible_branches]
        if "ALL" not in branches:
            query = query.filter(StudentProfile.branch.in_(branches))

    # Year filter
    if notice.eligible_years:
        years = []
        for y in notice.eligible_years:
            try:
                years.append(int(y))
            except ValueError:
                pass
        if years and "ALL" not in [str(y).upper() for y in notice.eligible_years]:
            query = query.filter(StudentProfile.year.in_(years))

    # CGPA filter
    if notice.min_cgpa and notice.min_cgpa > 0:
        query = query.filter(StudentProfile.cgpa >= notice.min_cgpa)

    return query.all()
