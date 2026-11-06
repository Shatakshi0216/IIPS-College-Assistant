"""
==============================================================================
FILE: backend/app/schemas/document.py
PURPOSE: Defines Pydantic validation schemas for Document responses, AI notice
         metadata, and Academic Resource catalog items.
==============================================================================
WHAT ARE NESTED SCHEMAS?
In this file, 'DocumentResponse' contains 'notice_metadata' and 'academic_resource'.
When FastAPI returns a document to the Flutter mobile app, Pydantic automatically
nests the AI-extracted details and academic details into a clean JSON structure:
{
  "id": 1,
  "title": "TCS Campus Placement Drive 2026",
  "category": "notice",
  "notice_metadata": {
    "deadline": "2026-10-25",
    "eligible_branches": ["CSE", "IT"],
    "min_cgpa": 7.5
  }
}
==============================================================================
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# 1. NOTICE METADATA SCHEMA (AI Extracted Data)
# ==============================================================================

class NoticeMetadataResponse(BaseModel):
    """
    Structured information extracted by Google Gemini for a notice.
    Sent to the student mobile feed to display badges, deadlines, and criteria.
    """
    id: int
    title: str = Field(..., example="TCS Campus Placement Drive 2026")
    summary: Optional[str] = Field(None, example="TCS invites final year students with 7.5+ CGPA...")
    action_required: Optional[str] = Field(None, example="Register on the NextStep portal before deadline.")
    deadline: Optional[str] = Field(None, example="2026-10-25")
    eligible_branches: List[str] = Field(default_factory=list, example=["CSE", "IT"])
    eligible_years: List[int] = Field(default_factory=list, example=[4])
    min_cgpa: float = Field(0.0, example=7.5)
    contact_info: Optional[str] = Field(None, example="placement@college.edu")
    is_urgent: bool = Field(False, example=True)

    # Enables automatic mapping from SQLAlchemy NoticeMetadata model to JSON
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. ACADEMIC RESOURCE SCHEMAS (Syllabus & Question Papers)
# ==============================================================================

class AcademicResourceCreate(BaseModel):
    """
    Schema for faculty uploading a syllabus or previous-year exam paper.
    Specifies which branch, semester, and course this PDF belongs to.
    """
    branch: str = Field(..., example="CSE", description="Target branch")
    year: int = Field(..., ge=1, le=5, example=3, description="Academic year")
    semester: int = Field(..., ge=1, le=10, example=5, description="Semester (1-10)")
    subject_name: str = Field(..., example="Operating Systems")
    subject_code: Optional[str] = Field(None, example="CS-501")
    resource_type: str = Field("syllabus", example="syllabus", description="'syllabus', 'question_paper', or 'notes'")
    exam_year: Optional[int] = Field(None, example=2024, description="Exam year (for question papers)")


class AcademicResourceResponse(BaseModel):
    """
    Catalog response for browsing academic documents in the library.
    """
    id: int
    branch: str
    year: int
    semester: int
    subject_name: str
    subject_code: Optional[str] = None
    resource_type: str
    exam_year: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. BASE DOCUMENT RESPONSE (Generic Document Representation)
# ==============================================================================

class DocumentResponse(BaseModel):
    """
    Complete document payload returned to the frontend.
    Includes base metadata, file details, and conditionally nested AI/academic info.
    """
    id: int
    title: str
    file_name: str
    file_path: str
    file_size_bytes: int
    category: str = Field(..., example="notice", description="notice, syllabus, question_paper, circular, rule")
    is_processed: bool = Field(..., description="True if text is extracted and vector embeddings are indexed")
    uploaded_by_id: Optional[int] = None
    created_at: datetime
    
    # Nested relationships (automatically populated if present)
    notice_metadata: Optional[NoticeMetadataResponse] = None
    academic_resource: Optional[AcademicResourceResponse] = None

    model_config = ConfigDict(from_attributes=True)
