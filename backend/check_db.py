"""
Database Verification Script
Inspects the SQLite database to confirm all tables are created
and shows the count and sample data for each table.

Run via:
    python check_db.py
"""
import sqlite3
import os

db_path = "college_assistant.db"

if not os.path.exists(db_path):
    print(f"❌ Database file '{db_path}' not found yet!")
    exit(1)

print(f"✅ Database file '{db_path}' exists! Size: {os.path.getsize(db_path)} bytes.\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Fetch all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

print("📋 Tables found in database:")
for idx, table in enumerate(tables, 1):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {idx}. Table: '{table}' ➔ {count} row(s)")

print("\n--------------------------------------------------")
print("🔍 Previewing Users Table:")
cursor.execute("SELECT id, email, full_name, role FROM users LIMIT 5;")
users = cursor.fetchall()
for u in users:
    print(f"   • ID: {u[0]} | Email: {u[1]} | Name: {u[2]} | Role: {u[3]}")

print("\n🔍 Previewing Student Profiles Table:")
cursor.execute("SELECT user_id, branch, year, semester, cgpa FROM student_profiles LIMIT 5;")
students = cursor.fetchall()
for s in students:
    print(f"   • User ID: {s[0]} | Branch: {s[1]} | Year: {s[2]} | Sem: {s[3]} | CGPA: {s[4]}")

print("--------------------------------------------------\n")
conn.close()
