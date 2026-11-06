"""
==============================================================================
FILE: backend/clean_production.py
PURPOSE: Resets the database and removes all mock seed data.
==============================================================================
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.config import settings

def clean_for_production():
    print("🧹 Wiping test accounts and mock notices...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables recreated fresh and empty!")

    # Clear vector store cache
    vector_meta_file = os.path.join(settings.VECTOR_STORE_DIR, "chunks_metadata.json")
    if os.path.exists(vector_meta_file):
        try:
            os.remove(vector_meta_file)
            print("✅ Vector chunk cache cleared!")
        except Exception:
            pass

    print("\n🎓 Production environment is 100% clean and ready for IIPS DAVV data!")

if __name__ == "__main__":
    clean_for_production()
