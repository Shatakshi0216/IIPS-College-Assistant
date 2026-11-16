"""
Academic Resources Router
Allows students to browse college-provided academic resources
(syllabi, previous-year question papers, lecture notes) filtered by
Branch -> Year/Semester -> Subject -> Resource Type.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, AcademicResource
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/resources", tags=["Academic Resources"])


@router.get("", response_model=List[DocumentResponse])
def get_academic_resources(
    branch: Optional[str] = Query(None, description="e.g. CSE, IT, ECE"),
    year: Optional[int] = Query(None, description="e.g. 1, 2, 3, 4"),
    semester: Optional[int] = Query(None, description="e.g. 1 to 8"),
    subject_name: Optional[str] = Query(None, description="Search by subject name"),
    resource_type: Optional[str] = Query(None, description="syllabus, question_paper, notes"),
    exam_year: Optional[int] = Query(None, description="e.g. 2023, 2024"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and filter academic resources hierarchically:
    Branch -> Year -> Semester -> Subject -> Type.
    """
    query = (
        db.query(Document)
        .join(AcademicResource, Document.id == AcademicResource.document_id)
    )

    if current_user.role == "student":
        profile = current_user.student_profile
        if profile is None:
            raise HTTPException(status_code=403, detail="Student academic profile is required")
        # Never trust student-supplied filters for access control. Force their profile.
        query = query.filter(
            ((AcademicResource.branch == profile.branch.upper()) | (AcademicResource.branch == "ALL")),
            AcademicResource.year == profile.year,
            AcademicResource.semester == profile.semester,
        )
    else:
        if branch:
            query = query.filter(
                (AcademicResource.branch == branch.upper()) | (AcademicResource.branch == "ALL")
            )
        if year:
            query = query.filter(AcademicResource.year == year)
        if semester:
            query = query.filter(AcademicResource.semester == semester)

    if resource_type:
        query = query.filter(AcademicResource.resource_type == resource_type.lower())

    if exam_year:
        query = query.filter(AcademicResource.exam_year == exam_year)

    if subject_name:
        query = query.filter(AcademicResource.subject_name.ilike(f"%{subject_name}%"))

    return query.order_by(Document.created_at.desc()).all()


@router.get("/subjects")
def get_unique_subjects(
    branch: Optional[str] = None,
    semester: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns subjects visible to the authenticated user."""
    query = db.query(AcademicResource.subject_name).distinct()
    if current_user.role == "student":
        profile = current_user.student_profile
        if profile is None:
            raise HTTPException(status_code=403, detail="Student academic profile is required")
        query = query.filter(
            ((AcademicResource.branch == profile.branch.upper()) | (AcademicResource.branch == "ALL")),
            AcademicResource.year == profile.year,
            AcademicResource.semester == profile.semester,
        )
    else:
        if branch:
            query = query.filter(
                (AcademicResource.branch == branch.upper()) | (AcademicResource.branch == "ALL")
            )
        if semester:
            query = query.filter(AcademicResource.semester == semester)

    results = query.all()
    return [r[0] for r in results if r[0]]
