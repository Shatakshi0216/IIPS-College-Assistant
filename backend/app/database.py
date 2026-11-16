
"""
Database Connection and Session Management.

Supports SQLite for local development and PostgreSQL for deployment.
Uses connection health checks to avoid reusing stale PostgreSQL connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings


# Read database URL from application settings.
db_url = settings.DATABASE_URL

# Normalize PostgreSQL URL for psycopg2 compatibility.
if db_url.startswith("postgres://"):
    db_url = db_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

# Preserve the existing channel_binding compatibility handling.
if "channel_binding" in db_url:
    db_url = db_url.replace("&channel_binding=require", "")
    db_url = db_url.replace("?channel_binding=require", "")


# Common engine settings.
engine_options = {
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    # SQLite settings for local development.
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

else:
    # PostgreSQL connection-pool settings.
    engine_options.update({
        "pool_recycle": 1800,
        "pool_timeout": 30,
        "connect_args": {
            "connect_timeout": 10
        }
    })


# Create one engine.
engine = create_engine(db_url, **engine_options)


# Verify the configured database connection.
# Do not silently switch to SQLite if PostgreSQL fails.
try:
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")

    if db_url.startswith("sqlite"):
        print("[OK] Connected to SQLite database")
    else:
        print("[OK] Connected to Cloud PostgreSQL")

except Exception as e:
    print(
        f"[DATABASE ERROR] Could not connect to configured database: "
        f"{type(e).__name__}: {e}"
    )
    raise


# Database session factory.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all SQLAlchemy models.
Base = declarative_base()


def get_db():
    """
    Provides a database session for each FastAPI request
    and closes it after the request finishes.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
