"""
==============================================================================
FILE: backend/app/models/user.py
PURPOSE: Defines database tables for Users, Students, and Faculty using SQLAlchemy.
==============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

# Import Base from database.py so SQLAlchemy knows these are database models
from app.database import Base


class User(Base):
    """
    The core User table.
    Stores login credentials and account status for everyone (Students, Faculty, Admins).
    """
    __tablename__ = "users"

    # Unique identifier for each user (Auto-incrementing 1, 2, 3...)
    id = Column(Integer, primary_key=True, index=True)

    # Email used for logging in (must be unique across all accounts)
    email = Column(String, unique=True, index=True, nullable=False)

    # We NEVER store plain passwords. We store the bcrypt salted hash.
    hashed_password = Column(String, nullable=False)

    # Full name of student or faculty (e.g. "Aarav Patel")
    full_name = Column(String, nullable=False)

    # Role defines permissions: "student", "faculty", or "admin"
    role = Column(String, default="student", nullable=False)

    # Allows deactivating an account without deleting data
    is_active = Column(Boolean, default=True)

    # Timestamp when the account was registered
    created_at = Column(DateTime, default=datetime.utcnow)

    # =========================================================================
    # Relationships: Links this User record to other tables
    # =========================================================================
    
    # 1-to-1 link to StudentProfile (uselist=False means single object, not a list)
    # ondelete="CASCADE" means if User is deleted, profile is deleted too
    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1-to-1 link to FacultyProfile
    faculty_profile = relationship(
        "FacultyProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1-to-Many link to documents uploaded by this user (faculty)
    uploaded_documents = relationship("Document", back_populates="uploader")

    # 1-to-Many link to targeted notifications received by this user (student)
    notifications = relationship("Notification", back_populates="student")


class StudentProfile(Base):
    """
    The StudentProfile table.
    Stores academic data required for the Eligibility Engine to filter notices.
    """
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking this profile directly to a row in 'users' table
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # College Roll Number / Enrollment ID (e.g., "21CS104")
    roll_number = Column(String, unique=True, index=True, nullable=True)

    # Engineering Branch: "CSE", "IT", "ECE", "ME", "CE"
    # Used to check: Does notice match student's branch?
    branch = Column(String, index=True, nullable=False)

    # Academic Year: 1, 2, 3, 4
    # Used to check: Is this notice meant for 4th years?
    year = Column(Integer, index=True, nullable=False)

    # Semester: 1 to 8
    semester = Column(Integer, nullable=False)

    # Section: "A", "B", etc.
    section = Column(String, nullable=True)

    # Current CGPA (e.g., 8.45)
    # Used to check: Does student meet notice's min_cgpa?
    cgpa = Column(Float, default=0.0)

    # Relationship back to the parent User record
    user = relationship("User", back_populates="student_profile")


class FacultyProfile(Base):
    """
    The FacultyProfile table.
    Stores departmental data for professors and college administrators.
    """
    __tablename__ = "faculty_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking this profile directly to a row in 'users' table
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Employee ID (e.g., "FAC-CS-101")
    employee_id = Column(String, unique=True, index=True, nullable=True)

    # Department name (e.g., "Computer Science & Engineering")
    department = Column(String, nullable=False)

    # Designation (e.g., "Assistant Professor", "Head of Department", "Placement Officer")
    designation = Column(String, nullable=True)

    # Relationship back to the parent User record
    user = relationship("User", back_populates="faculty_profile")
