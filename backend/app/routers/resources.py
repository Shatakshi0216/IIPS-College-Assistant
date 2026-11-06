"""
Academic Resources Router
Allows students to browse college-provided academic resources
(syllabi, previous-year question papers, lecture notes) filtered by
Branch -> Year/Semester -> Subject -> Resource Type.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, AcademicResource
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
    db: Session = Depends(get_db)
):
    """
    Search and filter academic resources hierarchically:
    Branch -> Year -> Semester -> Subject -> Type.
    """
    query = (
        db.query(Document)
        .join(AcademicResource, Document.id == AcademicResource.document_id)
    )

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
    db: Session = Depends(get_db)
):
    """Returns a list of unique subjects available for a given branch and semester."""
    query = db.query(AcademicResource.subject_name).distinct()
    if branch:
        query = query.filter(AcademicResource.branch == branch.upper())
    if semester:
        query = query.filter(AcademicResource.semester == semester)

    results = query.all()
    return [r[0] for r in results if r[0]]
