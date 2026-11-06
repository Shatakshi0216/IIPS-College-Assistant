"""
Schemas package initializer.
Exports Pydantic schemas for data validation and API response formatting.
"""
from app.schemas.user import (
    UserRegister,
    UserLogin,
    Token,
    TokenData,
    UserResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    FacultyProfileCreate,
    FacultyProfileResponse,
)
from app.schemas.document import (
    DocumentResponse,
    NoticeMetadataResponse,
    AcademicResourceResponse,
    AcademicResourceCreate,
)
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    SourceCitation,
    DocumentSummaryResponse,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
    "UserResponse",
    "StudentProfileCreate",
    "StudentProfileResponse",
    "FacultyProfileCreate",
    "FacultyProfileResponse",
    "DocumentResponse",
    "NoticeMetadataResponse",
    "AcademicResourceResponse",
    "AcademicResourceCreate",
    "ChatQueryRequest",
    "ChatQueryResponse",
    "SourceCitation",
    "DocumentSummaryResponse",
]
