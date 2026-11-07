"""
Documents Router
Handles PDF document uploads by faculty, automated text extraction,
Gemini metadata enrichment, vector chunk indexing, and document retrieval.
"""
import os
import shutil
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.document import Document, NoticeMetadata, AcademicResource
from app.models.notification import Notification
from app.schemas.document import DocumentResponse
from app.services.auth_service import get_current_user, require_role
from app.services.pdf_processor import extract_text_from_pdf, chunk_document_text
from app.services.gemini_extractor import extract_notice_metadata
from app.services.rag_engine import rag_engine
from app.services.eligibility_engine import get_eligible_students

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(..., description="notice, syllabus, question_paper, circular, or rule"),
    # Optional Academic Resource parameters:
    branch: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    semester: Optional[int] = Form(None),
    subject_name: Optional[str] = Form(None),
    subject_code: Optional[str] = Form(None),
    exam_year: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["faculty", "admin"]))
):
    """
    Upload an official PDF document (Faculty/Admin only).
    1. Validates and saves PDF to server storage.
    2. Extracts full text using PyPDF.
    3. If 'notice', Gemini extracts structured deadlines, eligibility & actions.
    4. Chunks and indexes document text into RAG vector store for instant Q&A.
    5. Dispatches notifications to eligible students.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported."
        )

    # 1. Determine subfolder and save file
    subfolder = "notices" if category.lower() == "notice" else "resources"
    dest_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(dest_dir, exist_ok=True)

    safe_filename = f"{int(time.time() * 1000)}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(dest_dir, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    # 2. Create base Document record
    new_doc = Document(
        title=title,
        file_name=file.filename,
        file_path=file_path,
        file_size_bytes=file_size,
        category=category.lower(),
        uploaded_by_id=current_user.id,
        is_processed=False
    )
    db.add(new_doc)
    db.flush()

    # 3. Extract text from PDF
    try:
        raw_text = extract_text_from_pdf(file_path)
    except Exception as e:
        raw_text = ""

    # 4. If category is Notice, Rule, or Circular, extract structured metadata with Gemini
    if category.lower() in ["notice", "rule", "circular"]:
        ai_data = extract_notice_metadata(raw_text) if raw_text else {}
        notice_meta = NoticeMetadata(
            document_id=new_doc.id,
            title=ai_data.get("title") or title,
            summary=ai_data.get("summary") or f"Official document: {title}. Please open the PDF to view all details.",
            action_required=ai_data.get("action_required"),
            deadline=ai_data.get("deadline"),
            eligible_branches=ai_data.get("eligible_branches", ["ALL"]),
            eligible_years=ai_data.get("eligible_years", [1, 2, 3, 4, 5]),
            min_cgpa=float(ai_data.get("min_cgpa") or 0.0),
            contact_info=ai_data.get("contact_info"),
            is_urgent=bool(ai_data.get("is_urgent", False))
        )
        db.add(notice_meta)
        db.flush()

        # Trigger notifications for eligible students
        eligible_students = get_eligible_students(db, notice_meta)
        for st in eligible_students:
            notif = Notification(
                student_id=st.user_id,
                document_id=new_doc.id,
                title=f"New Notice: {notice_meta.title}",
                message=notice_meta.summary or "New college notice relevant to you has been published."
            )
            db.add(notif)

    # 5. If category is Syllabus / Question Paper, store academic resource metadata
    elif category.lower() in ["syllabus", "question_paper", "notes"]:
        if not branch or not year or not semester or not subject_name:
            # Provide sensible defaults if not filled
            branch = branch or "ALL"
            year = year or 1
            semester = semester or 1
            subject_name = subject_name or title

        resource = AcademicResource(
            document_id=new_doc.id,
            branch=branch.upper(),
            year=year,
            semester=semester,
            subject_name=subject_name,
            subject_code=subject_code,
            resource_type=category.lower(),
            exam_year=exam_year
        )
        db.add(resource)

    # 6. Index text chunks into RAG Vector Store
    if raw_text:
        chunks = chunk_document_text(
            text=raw_text,
            document_id=new_doc.id,
            document_title=title
        )
        rag_engine.add_document_chunks(chunks)
        new_doc.is_processed = True

    db.commit()
    db.refresh(new_doc)
    return new_doc


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists uploaded college documents, optionally filtered by category."""
    query = db.query(Document)
    if category:
        query = query.filter(Document.category == category.lower())
    return query.order_by(Document.created_at.desc()).limit(limit).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_by_id(document_id: int, db: Session = Depends(get_db)):
    """Retrieves metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/file")
def download_document_file(document_id: int, db: Session = Depends(get_db)):
    """Downloads or streams the PDF file for in-app viewing."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        filename=doc.file_name
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["faculty", "admin"]))
):
    """
    Deletes an uploaded document, its associated metadata, notifications,
    and the physical PDF file (Faculty/Admin only).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete associated notifications
    db.query(Notification).filter(Notification.document_id == document_id).delete(synchronize_session=False)

    # 2. Delete associated notice metadata
    db.query(NoticeMetadata).filter(NoticeMetadata.document_id == document_id).delete(synchronize_session=False)

    # 3. Delete associated academic resources
    db.query(AcademicResource).filter(AcademicResource.document_id == document_id).delete(synchronize_session=False)

    # 4. Remove physical file from disk if present
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 5. Delete document record
    doc_title = doc.title
    db.delete(doc)
    db.commit()

    return {"status": "success", "message": f"Document '{doc_title}' deleted successfully."}
