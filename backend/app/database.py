"""
Database Connection and Session Management
Supports SQLite out of the box (zero-configuration) and seamlessly connects to PostgreSQL when configured.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Normalize PostgreSQL URL for psycopg2 driver compatibility
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Clean channel_binding for Windows libpq compatibility if present
if "channel_binding" in db_url:
    db_url = db_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Resilient connection: test PostgreSQL; if offline/DNS fails, fall back to local SQLite
try:
    if not db_url.startswith("sqlite"):
        test_engine = create_engine(db_url, connect_args=connect_args)
        with test_engine.connect() as test_conn:
            pass
        engine = test_engine
        print("[OK] Connected to Cloud PostgreSQL (Neon)")
    else:
        engine = create_engine(db_url, connect_args=connect_args)
except Exception as e:
    print(f"[WARNING] Cloud PostgreSQL unreachable. Falling back to local SQLite. ({type(e).__name__})")
    db_url = "sqlite:///./college_assistant.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
    print("[OK] Running on local SQLite database (college_assistant.db)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy database models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a transactional database session per request,
    and ensures it is cleanly closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
