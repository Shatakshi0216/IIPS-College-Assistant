"""
Notices & Personalized Feed Router
Serves personalized notices tailored to individual student profiles
using the rule-based eligibility engine.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.document import Document, NoticeMetadata
from app.models.notification import Notification
from app.schemas.document import DocumentResponse
from app.services.auth_service import get_current_user
from app.services.eligibility_engine import is_student_eligible

router = APIRouter(prefix="/notices", tags=["Personalized Notices"])


@router.get("/feed", response_model=List[DocumentResponse])
def get_personalized_notice_feed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns notices personalized for the currently logged-in student.
    - If student: filters notices by student's branch, year, and CGPA.
    - If faculty/admin: returns all notices.
    """
    all_notices = (
        db.query(Document)
        .filter(Document.category == "notice")
        .order_by(Document.created_at.desc())
        .all()
    )

    if current_user.role != "student" or not current_user.student_profile:
        return all_notices

    # Apply eligibility rules for student
    student_profile = current_user.student_profile
    personalized_feed = []

    for doc in all_notices:
        if not doc.notice_metadata:
            # If no metadata yet, show by default
            personalized_feed.append(doc)
        elif is_student_eligible(student_profile, doc.notice_metadata):
            personalized_feed.append(doc)

    return personalized_feed


@router.get("/notifications")
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves targeted alerts and notifications dispatched for the logged-in student."""
    notifs = (
        db.query(Notification)
        .filter(Notification.student_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "document_id": n.document_id,
            "is_read": n.is_read,
            "created_at": n.created_at
        }
        for n in notifs
    ]


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a notification as read."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.student_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    return {"status": "success", "message": "Notification marked as read"}
