"""Centralized access rules for student-owned documents and shared college content."""
from typing import List
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.user import User
from app.services.eligibility_engine import is_student_eligible


def can_access_document(document: Document, user: User) -> bool:
    # Faculty/admin can manage and view all college documents.
    if user.role != "student":
        return True

    # A student's personal documents are visible only to that student.
    if document.uploaded_by_id == user.id:
        return True

    profile = user.student_profile
    if profile is None:
        return False

    # Official notices are shared only when the eligibility engine permits them.
    if document.category in ("notice", "rule", "circular"):
        if document.notice_metadata is None:
            return True
        return is_student_eligible(profile, document.notice_metadata)

    # Academic resources are restricted to the student's own branch/year/semester.
    resource = document.academic_resource
    if resource is not None:
        return (
            resource.branch.upper() in (profile.branch.upper(), "ALL")
            and resource.year == profile.year
            and resource.semester == profile.semester
        )

    return False


def get_accessible_document_ids(db: Session, user: User) -> List[int]:
    documents = db.query(Document).all()
    return [doc.id for doc in documents if can_access_document(doc, user)]
