"""
Test script to verify connection to the Neon PostgreSQL database.
Run via:
    python test_postgres.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from sqlalchemy import create_engine, text

db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

print(f"Connecting to: {db_url.split('@')[-1]} ...")

try:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()
        print("✅ Connected successfully to PostgreSQL via psycopg2!")
        print(f"PostgreSQL Version: {version[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    # Check if channel_binding caused it
    if "channel_binding" in db_url:
        clean_url = db_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
        print("\nTrying without channel_binding parameter...")
        try:
            engine2 = create_engine(clean_url)
            with engine2.connect() as conn2:
                result2 = conn2.execute(text("SELECT version();"))
                print(" Connected successfully without channel_binding!")
                print(f"PostgreSQL Version: {result2.fetchone()[0]}")
        except Exception as e2:
            print(f" Still failed: {e2}")
