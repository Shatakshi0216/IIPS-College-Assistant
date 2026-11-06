"""
Models package initializer.
Exports all SQLAlchemy models for clean imports and database table discovery.
"""
from app.models.user import User, StudentProfile, FacultyProfile
from app.models.document import Document, NoticeMetadata, AcademicResource
from app.models.notification import Notification

__all__ = [
    "User",
    "StudentProfile",
    "FacultyProfile",
    "Document",
    "NoticeMetadata",
    "AcademicResource",
    "Notification",
]
