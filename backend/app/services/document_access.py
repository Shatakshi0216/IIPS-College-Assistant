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

    # Academic resources: student can see resources for their own branch (any semester)
    # or resources tagged as "ALL" branch. This allows browsing resources
    # from other semesters too (useful for ATKT / revision / upcoming semester prep).
    resource = document.academic_resource
    if resource is not None:
        branch_match = resource.branch.upper() in (profile.branch.upper(), "ALL")
        return branch_match

    # For any other document types (notes, etc.) — allow access if document exists
    # This ensures admin-uploaded files are visible to all students
    return True


def get_accessible_document_ids(db: Session, user: User) -> List[int]:
    documents = db.query(Document).all()
    return [doc.id for doc in documents if can_access_document(doc, user)]
