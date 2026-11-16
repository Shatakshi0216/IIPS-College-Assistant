"""Document upload, retrieval, access control, and authenticated PDF delivery."""
import os
import time
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import Response, FileResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.document import Document, NoticeMetadata, AcademicResource
from app.models.notification import Notification
from app.schemas.document import DocumentResponse
from app.services.auth_service import get_current_user, require_role, create_access_token
from app.services.document_access import can_access_document
from app.services.pdf_processor import extract_text_from_pdf, extract_text_from_pdf_bytes, chunk_document_text
from app.services.gemini_extractor import extract_notice_metadata
from app.services.rag_engine import rag_engine
from app.services.eligibility_engine import get_eligible_students

router = APIRouter(prefix="/documents", tags=["Documents"])
MAX_PDF_BYTES = 25 * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(..., description="notice, syllabus, question_paper, circular, or rule"),
    branch: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    semester: Optional[int] = Form(None),
    subject_name: Optional[str] = Form(None),
    subject_code: Optional[str] = Form(None),
    exam_year: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["faculty", "admin"])),
):
    """Upload and index a PDF. PDF bytes are stored in PostgreSQL, not Render disk."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents (.pdf) are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF size must not exceed 25 MB.")

    category_value = category.lower().strip()
    safe_filename = f"{int(time.time() * 1000)}_{os.path.basename(file.filename).replace(' ', '_')}"
    new_doc = Document(
        title=title,
        file_name=os.path.basename(file.filename),
        file_path=f"database://documents/{safe_filename}",
        file_data=pdf_bytes,
        file_size_bytes=len(pdf_bytes),
        category=category_value,
        uploaded_by_id=current_user.id,
        is_processed=False,
    )
    db.add(new_doc)
    db.flush()

    try:
        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Unable to read the uploaded PDF: {exc}")

    if raw_text:
        new_doc.raw_text = raw_text

    if category_value in ["notice", "rule", "circular"]:
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
            is_urgent=bool(ai_data.get("is_urgent", False)),
        )
        db.add(notice_meta)
        db.flush()
        for student in get_eligible_students(db, notice_meta):
            db.add(Notification(
                student_id=student.user_id, document_id=new_doc.id,
                title=f"New Notice: {notice_meta.title}",
                message=notice_meta.summary or "New college notice relevant to you has been published.",
            ))
    elif category_value in ["syllabus", "question_paper", "notes"]:
        if not branch or not year or not semester or not subject_name:
            raise HTTPException(status_code=422, detail="Academic resources require branch, year, semester, and subject name.")
        db.add(AcademicResource(
            document_id=new_doc.id, branch=branch.upper(), year=year, semester=semester,
            subject_name=subject_name, subject_code=subject_code,
            resource_type=category_value, exam_year=exam_year,
        ))

    if raw_text:
        chunks = chunk_document_text(raw_text, new_doc.id, title)
        rag_engine.add_document_chunks(chunks)
        new_doc.is_processed = True

    db.commit()
    db.refresh(new_doc)
    return new_doc





@router.get("", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Faculty/admin see all documents; students see eligible shared content and their own files."""
    query = db.query(Document)

    if category:
        query = query.filter(Document.category == category.lower().strip())

    documents = query.order_by(Document.created_at.desc()).all()

    if current_user.role == "student":
        documents = [
            doc for doc in documents
            if can_access_document(doc, current_user)
        ]

    safe_limit = min(max(limit, 1), 100)
    return documents[:safe_limit]


@router.post("/{document_id}/download-ticket")
def create_download_ticket(
    document_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Issue a 3-minute, document-scoped URL ticket for opening the PDF externally."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not can_access_document(doc, current_user):
        raise HTTPException(status_code=404, detail="Document not found")
    ticket = create_access_token(
        {"sub": str(current_user.id), "scope": "document_download", "document_id": doc.id},
        expires_delta=timedelta(minutes=3),
    )
    return {"ticket": ticket}


@router.get("/{document_id}/file", name="download_document_file")
def download_document_file(
    document_id: int, ticket: str = Query(...), db: Session = Depends(get_db),
):
    """Serve a PDF only with a short-lived ticket issued to an authorized user."""
    try:
        payload = jwt.decode(ticket, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "document_download" or int(payload.get("document_id", -1)) != document_id:
            raise ValueError("Invalid download ticket")
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Download link expired or invalid")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not user or not doc or not can_access_document(doc, user):
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_data:
        return Response(
            content=bytes(doc.file_data), media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{doc.file_name}"', "Cache-Control": "private, no-store"},
        )
    # Backward compatibility for legacy records still present on persistent local storage.
    if doc.file_path and os.path.isfile(doc.file_path):
        return FileResponse(doc.file_path, media_type="application/pdf", filename=doc.file_name)
    raise HTTPException(status_code=404, detail="PDF file is unavailable. Please ask faculty to upload it again.")


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["faculty", "admin"])),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.query(Notification).filter(Notification.document_id == document_id).delete(synchronize_session=False)
    db.query(NoticeMetadata).filter(NoticeMetadata.document_id == document_id).delete(synchronize_session=False)
    db.query(AcademicResource).filter(AcademicResource.document_id == document_id).delete(synchronize_session=False)
    if doc.file_path and os.path.isfile(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass
    title = doc.title
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": f"Document '{title}' deleted successfully."}
