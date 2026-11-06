"""
Routers package initializer.
Exports all API routers for inclusion in the FastAPI app.
"""
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.notices import router as notices_router
from app.routers.resources import router as resources_router
from app.routers.chat import router as chat_router

__all__ = [
    "auth_router",
    "documents_router",
    "notices_router",
    "resources_router",
    "chat_router",
]
