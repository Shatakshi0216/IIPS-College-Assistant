"""
FastAPI Application Entry Point
Initializes FastAPI, mounts routers, configures CORS, and provisions database tables.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base
import app.models  # Ensures all models are registered with Base.metadata
from app.routers import (
    auth_router,
    documents_router,
    notices_router,
    resources_router,
    chat_router,
)

# 1. Create database tables on application startup
Base.metadata.create_all(bind=engine)

def init_production_db():
    """
    Cleans up initial mock data and provisions the official IIPS DAVV Master Admin.
    """
    from app.database import SessionLocal
    from app.models.user import User, StudentProfile, FacultyProfile
    from app.models.document import Document, NoticeMetadata, AcademicResource
    from app.models.notification import Notification
    from app.services.auth_service import get_password_hash

    db = SessionLocal()
    try:
        # 1. Clean up mock/test documents and notices
        mock_keywords = ["Sports", "Operating Systems", "TCS", "Attendance"]
        for kw in mock_keywords:
            mock_docs = db.query(Document).filter(Document.title.ilike(f"%{kw}%")).all()
            for doc in mock_docs:
                db.query(Notification).filter(Notification.document_id == doc.id).delete(synchronize_session=False)
                db.query(NoticeMetadata).filter(NoticeMetadata.document_id == doc.id).delete(synchronize_session=False)
                db.query(AcademicResource).filter(AcademicResource.document_id == doc.id).delete(synchronize_session=False)
                if doc.file_path and os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except Exception:
                        pass
                db.delete(doc)

        # 2. Clean up sample dummy users
        mock_emails = ["faculty@college.edu", "student@college.edu", "me_student@college.edu"]
        mock_users = db.query(User).filter(User.email.in_(mock_emails)).all()
        for u in mock_users:
            db.query(StudentProfile).filter(StudentProfile.user_id == u.id).delete(synchronize_session=False)
            db.query(FacultyProfile).filter(FacultyProfile.user_id == u.id).delete(synchronize_session=False)
            db.delete(u)

        # 3. Create official Master Admin account for IIPS DAVV if not exists
        admin_email = "admin@iips.davv.ac.in"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("Admin@IIPS2026"),
                full_name="IIPS DAVV Administrator",
                role="faculty",
                is_active=True
            )
            db.add(admin_user)
            db.flush()

            admin_profile = FacultyProfile(
                user_id=admin_user.id,
                employee_id="IIPS-ADM-01",
                department="Academic & Examination Affairs",
                designation="Director / Chief Coordinator"
            )
            db.add(admin_profile)
            print(f"[OK] Master Admin created: {admin_email} / Admin@IIPS2026")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARNING] Database initialization note: {e}")
    finally:
        db.close()

# Run initialization
try:
    init_production_db()
except Exception as e:
    print(f"[WARNING] Startup init deferred: {e}")

# Ensure upload and vector directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "notices"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "resources"), exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)

# 2. Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## AI-Powered College Information & Notice Assistant API
    
    A comprehensive backend platform featuring:
    * **Role-Based Authentication** for Students and Faculty.
    * **PDF Document Processing** with automated metadata extraction powered by Google Gemini.
    * **Personalized Notice Feeds** matching student branches, years, and CGPA.
    * **Academic Resources Catalog** for syllabi and previous-year question papers.
    * **RAG-Powered AI Chatbot** answering questions grounded strictly in official college documents.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. Configure CORS (Cross-Origin Resource Sharing)
# Allows the Flutter mobile app, web browsers, and local emulators to communicate freely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Mount Uploads and Static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 5. Register API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(notices_router, prefix=settings.API_V1_STR)
app.include_router(resources_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
@app.get("/app", include_in_schema=False)
def serve_mobile_app():
    """Serves the responsive mobile app interface for testing with no-cache headers."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        response = FileResponse(index_file)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    """Root health check endpoint."""
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }
