"""
==============================================================================
FILE: backend/reset_db.py
PURPOSE: Wipes all test accounts, mock notices, and cached vector chunks.
         Leaves a clean, fresh production database ready for actual college data.
==============================================================================
"""

import os
import sys

# Ensure backend root is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.config import settings

def reset_database():
    print("🧹 Cleaning database tables...")
    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)
    # Recreate all fresh empty tables
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables wiped and recreated clean!")

    # Clean vector store
    vector_meta_file = os.path.join(settings.VECTOR_STORE_DIR, "chunks_metadata.json")
    if os.path.exists(vector_meta_file):
        try:
            os.remove(vector_meta_file)
            print("✅ Vector store cache cleared!")
        except Exception as e:
            print(f"Notice: Could not delete vector cache: {e}")

    print("\n🎉 Database is now 100% clean and ready for production data!")

if __name__ == "__main__":
    confirm = input("⚠️ Are you sure you want to wipe all data for production? (y/N): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled.")
