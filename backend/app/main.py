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
    """Serves the responsive mobile app interface for testing."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
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
