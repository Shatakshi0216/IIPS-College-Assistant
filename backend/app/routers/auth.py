"""
==============================================================================
FILE: backend/app/routers/auth.py
PURPOSE: Authentication Endpoints (Router).
         Exposes REST API routes for User Registration, Login, and Profile Retrieval.
==============================================================================
ENDPOINTS IN THIS ROUTER:
1. POST /api/v1/auth/register    ➔ Create new Student or Faculty account.
2. POST /api/v1/auth/login       ➔ Login for Swagger UI (OAuth2 form-data).
3. POST /api/v1/auth/login-json  ➔ Login for Flutter Mobile App (JSON body).
4. GET  /api/v1/auth/me          ➔ Get current logged-in user profile (Protected).
==============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, StudentProfile, FacultyProfile
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)

# Prefix all routes with /auth
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==============================================================================
# 1. USER REGISTRATION
# ==============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Student or Faculty user"
)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new account in PostgreSQL:
    1. Validates that the email is not already registered.
    2. Hashes the plain-text password using bcrypt.
    3. Saves the User row in 'users' table.
    4. Automatically creates the linked 'student_profiles' or 'faculty_profiles' row.
    """
    # Step 1: Check for duplicate email
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Step 2: Hash the password (Never store plain passwords!)
    hashed_pwd = get_password_hash(user_in.password)
    
    # Step 3: Create parent User record
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role.lower(),
    )
    db.add(new_user)
    db.flush()  # flushes SQL so new_user.id is generated before creating the profile

    # Step 4: Create linked role-specific profile
    if new_user.role == "student":
        profile_data = user_in.student_profile
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student profile information (branch, year, semester) is required for student accounts."
            )
        student_profile = StudentProfile(
            user_id=new_user.id,
            roll_number=profile_data.roll_number,
            branch=profile_data.branch.upper(),
            year=profile_data.year,
            semester=profile_data.semester,
            section=profile_data.section,
            cgpa=profile_data.cgpa,
        )
        db.add(student_profile)

    elif new_user.role in ["faculty", "admin"]:
        profile_data = user_in.faculty_profile
        faculty_profile = FacultyProfile(
            user_id=new_user.id,
            employee_id=profile_data.employee_id if profile_data else None,
            department=profile_data.department if profile_data else "General",
            designation=profile_data.designation if profile_data else "Faculty",
        )
        db.add(faculty_profile)

    # Step 5: Commit transaction to PostgreSQL
    db.commit()
    db.refresh(new_user)
    return new_user


# ==============================================================================
# 2. LOGIN (FOR SWAGGER UI - Form Data)
# ==============================================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Login for Swagger UI (Form Data)"
)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Standard OAuth2 password flow login endpoint.
    Used by Swagger UI's green 'Authorize' button.
    Expects form fields: username (email) and password.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create signed JWT token
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "user_id": user.id,
    }


# ==============================================================================
# 3. LOGIN (FOR FLUTTER MOBILE APP - JSON Body)
# ==============================================================================

@router.post(
    "/login-json",
    response_model=Token,
    summary="Login for Mobile App (JSON Body)"
)
def login_with_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Standard JSON login endpoint for the Flutter mobile application.
    Expects JSON: { "email": "student@college.edu", "password": "..." }
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "user_id": user.id,
    }


# ==============================================================================
# 4. CURRENT LOGGED-IN USER PROFILE (PROTECTED ROUTE)
# ==============================================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get profile of currently logged-in user"
)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Protected route: requires 'Authorization: Bearer <token>' header.
    Returns the user's account details and full academic/faculty profile.
    """
    return current_user
