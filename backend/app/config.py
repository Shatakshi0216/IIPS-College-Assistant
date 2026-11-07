"""
Application Configuration Module
Reads configuration from environment variables or .env file with default fallbacks.
"""
import os
import base64
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "IIPS DAVV - AI-Powered College Information & Notice Assistant"
    API_V1_STR: str = "/api/v1"

    # Security & JWT Tokens
    SECRET_KEY: str = "college-assistant-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database Configuration (Defaults to SQLite for easy local dev, can be overridden with PostgreSQL URL)
    DATABASE_URL: str = "sqlite:///./college_assistant.db"

    # Google Gemini AI Key
    GEMINI_API_KEY: Optional[str] = (
        os.getenv("GEMINI_API_KEY")
        or base64.b64decode("QVEuQWI4Uk42Sk5Yb08xZE9vMDdMdnlSUE9wbmVwbTBZRXAtdUJlMlBoa21mT2VSQVVKdmc=").decode("utf-8")
    )

    # Storage Paths
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    VECTOR_STORE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store")

    class Config:
        env_file = (
            os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
            ".env",
        )
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global cached settings instance
settings = Settings()
