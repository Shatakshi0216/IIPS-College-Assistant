"""
Sample Data Seeder Script
Populates the database with sample faculty, students, notices, and academic resources
so you can test the application, personalized feeds, and authentication immediately!

Run via:
    python seed_data.py
"""
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Base, engine
from app.models.user import User, StudentProfile, FacultyProfile
from app.models.document import Document, NoticeMetadata, AcademicResource
from app.models.notification import Notification
from app.services.auth_service import get_password_hash
from app.services.rag_engine import rag_engine

def seed():
    print("🌱 Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("ℹ️ Database already contains data. Skipping seeding.")
        db.close()
        return

    print("Creating sample faculty user...")
    faculty_user = User(
        email="faculty@college.edu",
        hashed_password=get_password_hash("faculty123"),
        full_name="Dr. Sarah Sharma",
        role="faculty"
    )
    db.add(faculty_user)
    db.flush()

    faculty_profile = FacultyProfile(
        user_id=faculty_user.id,
        employee_id="FAC-CS-101",
        department="Computer Science & Engineering",
        designation="Associate Professor & Placement Coordinator"
    )
    db.add(faculty_profile)

    print("Creating sample 4th-year CSE student user...")
    cse_student = User(
        email="student@college.edu",
        hashed_password=get_password_hash("student123"),
        full_name="Aarav Patel",
        role="student"
    )
    db.add(cse_student)
    db.flush()

    cse_profile = StudentProfile(
        user_id=cse_student.id,
        roll_number="21CS104",
        branch="CSE",
        year=4,
        semester=7,
        section="A",
        cgpa=8.45
    )
    db.add(cse_profile)

    print("Creating sample 2nd-year Mechanical student user...")
    me_student = User(
        email="me_student@college.edu",
        hashed_password=get_password_hash("student123"),
        full_name="Rohan Verma",
        role="student"
    )
    db.add(me_student)
    db.flush()

    me_profile = StudentProfile(
        user_id=me_student.id,
        roll_number="23ME042",
        branch="ME",
        year=2,
        semester=3,
        section="B",
        cgpa=7.20
    )
    db.add(me_profile)

    print("Creating sample college notices...")
    # Notice 1: Placement drive for 4th year CSE/IT with CGPA >= 7.5
    doc_placement = Document(
        title="TCS Digital & Ninja Campus Placement Drive 2026",
        file_name="TCS_Placement_Drive_2026.pdf",
        file_path="uploads/notices/tcs_placement.pdf",
        file_size_bytes=102400,
        category="notice",
        uploaded_by_id=faculty_user.id,
        is_processed=True
    )
    db.add(doc_placement)
    db.flush()

    meta_placement = NoticeMetadata(
        document_id=doc_placement.id,
        title="TCS Digital & Ninja Campus Placement Drive 2026",
        summary="Tata Consultancy Services (TCS) invites applications for Ninja and Digital developer profiles. Registration must be completed on NextStep portal.",
        action_required="Complete registration on NextStep portal and submit CT/DT reference number to T&P cell.",
        deadline="2026-10-25",
        eligible_branches=["CSE", "IT"],
        eligible_years=[4],
        min_cgpa=7.5,
        contact_info="placement@college.edu",
        is_urgent=True
    )
    db.add(meta_placement)

    # Dispatch notification for Aarav (CSE 4th year, CGPA 8.45 >= 7.5)
    notif1 = Notification(
        student_id=cse_student.id,
        document_id=doc_placement.id,
        title="Eligible: TCS Campus Placement Drive 2026",
        message="You are eligible for the TCS Digital & Ninja recruitment drive. Deadline: Oct 25, 2026."
    )
    db.add(notif1)

    # Notice 2: General Notice for all students (Sports Meet)
    doc_sports = Document(
        title="Annual Inter-College Sports & Athletics Meet 2026",
        file_name="Sports_Meet_2026.pdf",
        file_path="uploads/notices/sports_meet.pdf",
        file_size_bytes=84200,
        category="notice",
        uploaded_by_id=faculty_user.id,
        is_processed=True
    )
    db.add(doc_sports)
    db.flush()

    meta_sports = NoticeMetadata(
        document_id=doc_sports.id,
        title="Annual Inter-College Sports & Athletics Meet 2026",
        summary="Registrations are open for track and field, badminton, football, and cricket tournaments. Open to all students.",
        action_required="Submit participation forms at the Sports Complex office.",
        deadline="2026-11-05",
        eligible_branches=["ALL"],
        eligible_years=[1, 2, 3, 4],
        min_cgpa=0.0,
        contact_info="sports@college.edu",
        is_urgent=False
    )
    db.add(meta_sports)

    # Notice 3: Academic Regulation - Attendance Requirement
    doc_attendance = Document(
        title="Academic Guidelines: Mandatory 75% Attendance Requirement",
        file_name="Attendance_Rules_2026.pdf",
        file_path="uploads/notices/attendance_rules.pdf",
        file_size_bytes=51200,
        category="rule",
        uploaded_by_id=faculty_user.id,
        is_processed=True
    )
    db.add(doc_attendance)
    db.flush()

    # Index sample chunks in RAG engine
    rag_engine.add_document_chunks([
        {
            "text": "Academic Regulation 4.2: Every student must maintain a minimum of 75% attendance in aggregate across all lecture and lab courses to be eligible to appear for the End-Semester Examination. A condonation of up to 10% may be granted by the Dean of Academic Affairs only on medical grounds with valid documentation.",
            "metadata": {
                "document_id": doc_attendance.id,
                "document_title": "Academic Guidelines: Mandatory 75% Attendance Requirement",
                "chunk_index": 0
            }
        },
        {
            "text": "TCS Campus Placement Drive 2026: Eligible streams are B.Tech CSE and IT (Final Year / 7th Semester). Minimum CGPA required is 7.5 with no active backlogs. The online aptitude test will be held on October 28, 2026. The registration deadline is October 25, 2026.",
            "metadata": {
                "document_id": doc_placement.id,
                "document_title": "TCS Digital & Ninja Campus Placement Drive 2026",
                "chunk_index": 0
            }
        }
    ])

    # Sample Academic Resource: Syllabus
    doc_syllabus = Document(
        title="Operating Systems (CS-501) Syllabus & Reference Books",
        file_name="CS501_Operating_Systems_Syllabus.pdf",
        file_path="uploads/resources/os_syllabus.pdf",
        file_size_bytes=64000,
        category="syllabus",
        uploaded_by_id=faculty_user.id,
        is_processed=True
    )
    db.add(doc_syllabus)
    db.flush()

    res_syllabus = AcademicResource(
        document_id=doc_syllabus.id,
        branch="CSE",
        year=3,
        semester=5,
        subject_name="Operating Systems",
        subject_code="CS-501",
        resource_type="syllabus"
    )
    db.add(res_syllabus)

    db.commit()
    db.close()
    print("✅ Sample data successfully seeded!")
    print("\nTest User Accounts Created:")
    print("  1. Faculty: faculty@college.edu  / password: faculty123")
    print("  2. Student (CSE, 4th Year, 8.45 CGPA): student@college.edu / password: student123")
    print("  3. Student (ME, 2nd Year, 7.20 CGPA): me_student@college.edu / password: student123")

if __name__ == "__main__":
    seed()
