"""
AI Chat & RAG Assistant Router
Powers student natural language queries against official college documents
and generates concise summaries of lengthy circulars.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    DocumentSummaryResponse,
)
from app.services.rag_engine import rag_engine
from app.services.pdf_processor import extract_text_from_pdf, extract_text_from_pdf_bytes
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.document_access import can_access_document, get_accessible_document_ids

router = APIRouter(prefix="/chat", tags=["AI College Assistant (RAG)"])


@router.post("/ask", response_model=ChatQueryResponse)
def ask_college_assistant(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask any question about college notices, examination guidelines, attendance rules,
    or scholarships. Uses RAG to find relevant document excerpts and grounds the answer using Gemini.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    allowed_ids = get_accessible_document_ids(db, current_user)
    if request.document_id is not None and request.document_id not in allowed_ids:
        raise HTTPException(status_code=404, detail="Document not found")

    response = rag_engine.answer_question(
        query=request.query,
        document_id=request.document_id,
        db=db,
        allowed_document_ids=allowed_ids,
    )

    return response


@router.get("/summarize/{document_id}", response_model=DocumentSummaryResponse)
def summarize_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a concise AI summary of an uploaded college document from its actual PDF content.
    Always regenerates from the PDF so summaries reflect real document content, not stored placeholders.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not can_access_document(doc, current_user):
        raise HTTPException(status_code=404, detail="Document not found")

    # Always regenerate from actual PDF content.
    # The stored notice_metadata.summary may be a generic placeholder from upload time.
    raw_text = ""
    try:
        raw_text = doc.raw_text or ""
    except Exception:
        pass
    if not raw_text and doc.file_data:
        try:
            raw_text = extract_text_from_pdf_bytes(bytes(doc.file_data))
        except Exception:
            raw_text = ""
    if not raw_text and doc.file_path:
        try:
            raw_text = extract_text_from_pdf(doc.file_path)
        except Exception:
            raw_text = ""

    summary_data = rag_engine.summarize_document(doc.title, raw_text, document_id=doc.id)

    # Build eligibility string from stored metadata if available
    eligibility_str = None
    if doc.notice_metadata:
        branches = doc.notice_metadata.eligible_branches or ["ALL"]
        years = doc.notice_metadata.eligible_years or ["ALL"]
        cgpa = doc.notice_metadata.min_cgpa
        eligibility_str = (
            f"Branches: {', '.join(str(b) for b in branches)}, "
            f"Years: {', '.join(str(y) for y in years)}"
            + (f", Min CGPA: {cgpa}" if cgpa and cgpa > 0 else "")
        )

    return {
        "document_id": doc.id,
        "title": doc.title,
        "summary": summary_data.get("summary", "Summary unavailable."),
        "key_deadlines": (
            summary_data.get("key_deadlines")
            or (doc.notice_metadata.deadline if doc.notice_metadata else None)
        ),
        "eligibility": eligibility_str or summary_data.get("eligibility"),
        "action_required": (
            summary_data.get("action_required")
            or (doc.notice_metadata.action_required if doc.notice_metadata else None)
        ),
    }
