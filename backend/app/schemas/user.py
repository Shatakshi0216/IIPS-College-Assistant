"""
==============================================================================
FILE: backend/app/schemas/user.py
PURPOSE: Defines Pydantic validation schemas for User registration, login,
         and safe public responses.
==============================================================================
WHAT IS PYDANTIC?
In FastAPI, Pydantic acts as the "bouncer" and the "filter":
1. REQUEST BOUNCER: When someone sends data (JSON) to our API, Pydantic checks:
   - Is email properly formatted? (e.g. user@college.edu)
   - Is password at least 6 characters?
   - Is CGPA between 0.0 and 10.0?
   If invalid, FastAPI immediately rejects the request with a 422 error!
   
2. RESPONSE FILTER: When sending data back to the client/app, Pydantic ensures
   we NEVER expose secret database fields like 'hashed_password'.
==============================================================================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==============================================================================
# 1. PROFILE CREATION SCHEMAS (Embedded inside Registration)
# ==============================================================================

class StudentProfileCreate(BaseModel):
    """
    Academic information required when registering a new Student account.
    """
    roll_number: Optional[str] = Field(None, example="21CS104")
    branch: str = Field(..., example="CSE", description="Engineering branch (e.g. CSE, IT, ME)")
    year: int = Field(..., ge=1, le=5, example=4, description="Current academic year (1-5)")
    semester: int = Field(..., ge=1, le=10, example=7, description="Current semester (1-10)")
    section: Optional[str] = Field("A", example="A")
    cgpa: float = Field(0.0, ge=0.0, le=10.0, example=8.25, description="CGPA on a 10.0 scale")


class FacultyProfileCreate(BaseModel):
    """
    Departmental information required when registering a new Faculty account.
    """
    employee_id: Optional[str] = Field(None, example="FAC-CS-101")
    department: str = Field(..., example="Computer Science & Engineering")
    designation: Optional[str] = Field("Assistant Professor", example="Assistant Professor")


# ==============================================================================
# 2. AUTHENTICATION REQUEST SCHEMAS (Data arriving from frontend)
# ==============================================================================

class UserRegister(BaseModel):
    """
    The JSON payload expected when a user hits POST /api/v1/auth/register.
    Accepts student_profile or faculty_profile based on the selected role.
    """
    email: EmailStr = Field(..., example="student@college.edu")
    password: str = Field(..., min_length=6, example="student123", description="Minimum 6 characters")
    full_name: str = Field(..., example="Aarav Patel")
    role: str = Field("student", example="student", description="'student', 'faculty', or 'admin'")
    
    # Nested profile objects (optional depending on role)
    student_profile: Optional[StudentProfileCreate] = None
    faculty_profile: Optional[FacultyProfileCreate] = None


class UserLogin(BaseModel):
    """
    The JSON payload for logging in.
    """
    email: EmailStr = Field(..., example="student@college.edu")
    password: str = Field(..., example="student123")


# ==============================================================================
# 3. TOKEN & SESSION SCHEMAS
# ==============================================================================

class Token(BaseModel):
    """
    The response returned after successful login containing the JWT bearer token.
    The Flutter mobile app stores this token locally to authenticate future requests.
    """
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class TokenData(BaseModel):
    """
    Data extracted and decoded from the inside of a JWT token payload.
    """
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ==============================================================================
# 4. PUBLIC RESPONSE SCHEMAS (Data sent back to frontend)
# ==============================================================================

class StudentProfileResponse(BaseModel):
    """Public academic profile info (safe to send over API)."""
    id: int
    roll_number: Optional[str] = None
    branch: str
    year: int
    semester: int
    section: Optional[str] = None
    cgpa: float

    # from_attributes=True enables converting SQLAlchemy models directly into Pydantic models
    model_config = ConfigDict(from_attributes=True)


class FacultyProfileResponse(BaseModel):
    """Public faculty profile info (safe to send over API)."""
    id: int
    employee_id: Optional[str] = None
    department: str
    designation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """
    The safe, sanitized user object sent back to the frontend.
    NOTICE: 'hashed_password' is deliberately excluded so it is NEVER leaked!
    """
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    student_profile: Optional[StudentProfileResponse] = None
    faculty_profile: Optional[FacultyProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
