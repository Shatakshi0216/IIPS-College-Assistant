"""
==============================================================================
FILE: backend/app/services/auth_service.py
PURPOSE: Authentication & Security Controller.
         Handles Password Hashing (bcrypt), JWT Token Generation & Verification,
         and Role-Based Route Protection (RBAC).
==============================================================================
HOW JWT AUTHENTICATION WORKS IN THIS PROJECT:
1. User logs in with email & password at POST /api/v1/auth/login.
2. If credentials are correct, server generates a signed JSON Web Token (JWT).
3. The JWT contains: { "sub": user_id, "role": "student", "exp": expiry_time }.
4. The client (Flutter App) saves this token and sends it in the HTTP header:
      Authorization: Bearer <token>
5. On protected routes, FastAPI's 'get_current_user' dependency decodes the token,
   fetches the user from PostgreSQL, and ensures they have active permissions.
==============================================================================
"""

from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

# OAuth2PasswordBearer tells FastAPI that the token should be extracted from the 'Authorization' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# ==============================================================================
# 1. PASSWORD SECURITY (BCRYPT)
# ==============================================================================

def get_password_hash(password: str) -> str:
    """
    Encrypts a plain-text password using a random salt and the bcrypt algorithm.
    - Salt: Random bytes added to prevent rainbow table attacks.
    - Bcrypt standard enforces a 72-byte max length; we slice to avoid errors.
    """
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is standard secure work factor
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plain password entered at login matches the stored bcrypt hash.
    Uses constant-time comparison to prevent timing attacks.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# ==============================================================================
# 2. JWT TOKEN GENERATION
# ==============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a cryptographically signed JSON Web Token (JWT).
    Payload includes the user ID, role, and expiration timestamp.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Sign token with our SECRET_KEY using HS256 algorithm
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# ==============================================================================
# 3. FASTAPI DEPENDENCIES (Route Guards)
# ==============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI Dependency:
    1. Extracts 'Bearer <token>' from the request headers.
    2. Verifies signature using SECRET_KEY.
    3. Checks if token has expired.
    4. Fetches the User from PostgreSQL.
    5. Returns the user object, or raises 401 Unauthorized if invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and verify token signature
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise credentials_exception
            
        user_id = int(user_id_str)
        role: str = payload.get("role")
        token_data = TokenData(user_id=user_id, role=role)
        
    except (JWTError, ValueError):
        raise credentials_exception

    # Query the user from the database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user


def require_role(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) Dependency Factory.
    Use in route definitions to restrict endpoints to specific user roles.
    
    Example:
        @router.post("/upload")
        def upload_doc(current_user: User = Depends(require_role(["faculty", "admin"]))):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: this action requires one of {allowed_roles} roles. Your role is '{current_user.role}'.",
            )
        return current_user
        
    return role_checker
