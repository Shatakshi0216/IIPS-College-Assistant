# AI-Powered College Information & Notice Assistant

An end-to-end intelligent college companion system featuring a **Python FastAPI** backend, **PostgreSQL** database (Cloud Neon), **Google Gemini** document understanding, **LangChain & FAISS** RAG pipeline, and a **Flutter** mobile client.

---

## 🎯 Project Requirements Fulfillment (FR-01 to FR-07)

| Requirement | Description | Implementation in Codebase |
| :--- | :--- | :--- |
| **FR-01: Authentication** | Secure role-based login (Student & Faculty). Student profiles hold branch, year, semester, section, CGPA. Faculty accounts manage uploads. | `backend/app/routers/auth.py`<br>`backend/app/models/user.py`<br>`mobile_app/lib/screens/login_screen.dart`<br>`mobile_app/lib/screens/register_screen.dart` |
| **FR-02: Document Management** | Authorized faculty upload PDF notices, syllabi, circulars, rules, scholarships, placements. Category-based organization. | `backend/app/routers/documents.py`<br>`backend/app/services/pdf_processor.py`<br>`mobile_app/lib/screens/upload_screen.dart` |
| **FR-03: AI Document Understanding** | Extract text from PDFs, Gemini converts to structured JSON: category, deadlines, eligible branch/year, min CGPA, required actions. | `backend/app/services/gemini_extractor.py`<br>`backend/app/models/document.py` (`NoticeMetadata`) |
| **FR-04: Personalized Notices & Alerts** | Rule-based engine matches notice criteria with student profile (branch, year, CGPA). Targeted student alerts. | `backend/app/services/eligibility_engine.py`<br>`backend/app/routers/notices.py`<br>`mobile_app/lib/screens/notice_feed_screen.dart`<br>`mobile_app/lib/screens/notifications_screen.dart` |
| **FR-05: Academic Resources** | Browse college syllabus and previous-year question papers filtered by Branch → Year/Semester → Subject → Type. | `backend/app/routers/resources.py`<br>`backend/app/models/document.py` (`AcademicResource`)<br>`mobile_app/lib/screens/academic_resources_screen.dart` |
| **FR-06: RAG AI Assistant** | Grounded question answering: searches document chunks in vector store and prompts Gemini with official context + citations. | `backend/app/services/rag_engine.py`<br>`backend/app/routers/chat.py`<br>`mobile_app/lib/screens/ai_chat_screen.dart` |
| **FR-07: Summarization & Search** | Semantic search across documents and concise AI summaries highlighting eligibility, deadlines, instructions. | `backend/app/services/rag_engine.py`<br>`backend/app/routers/chat.py` (`/summarize/{id}`) |

---

## 📁 Repository Structure

```
Minor Project/
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── config.py              # Settings & environment variables (.env)
│   │   ├── database.py            # SQLAlchemy PostgreSQL connection (Neon Cloud)
│   │   ├── models/                # Database tables (Users, Profiles, Documents, Notices)
│   │   ├── schemas/               # Pydantic v2 request & response schemas
│   │   ├── services/              # Auth, PDF Processing, Gemini AI, RAG & Matching
│   │   │   ├── auth_service.py    # Bcrypt password hashing & JWT token logic
│   │   │   ├── pdf_processor.py   # PyPDF extraction & LangChain text chunking
│   │   │   ├── gemini_extractor.py# Gemini AI structured JSON metadata extraction
│   │   │   ├── rag_engine.py      # Vector search + Gemini grounded Q&A
│   │   │   └── eligibility_engine.py # Rule-based matching engine
│   │   ├── routers/               # API Endpoints (/auth, /documents, /notices, /resources, /chat)
│   │   └── main.py                # FastAPI entrypoint, Static files, CORS middleware
│   ├── uploads/                   # Stored PDF documents (notices/ and resources/)
│   ├── vector_store/              # Persisted chunk indices
│   ├── requirements.txt           # Python dependencies
│   ├── seed_data.py               # Seed script with test users and notices
│   └── test_postgres.py           # Verification script for database connection
│
├── mobile_app/                    # Flutter Mobile Application
│   ├── lib/
│   │   ├── config/api_config.dart # Base URL & REST endpoints
│   │   ├── models/                # Dart models (User, Document, Notification, Chat)
│   │   ├── services/              # AuthService, DocumentService, ChatService
│   │   ├── screens/               # Login, Register, Notice Feed, Resources, AI Chat, Upload
│   │   └── main.dart              # Flutter entry point & Material 3 theme
│   └── pubspec.yaml               # Flutter package dependencies
│
└── README.md                      # Comprehensive project guide
```

---

## 🚀 Running the Project

### Part 1: Start the FastAPI Backend

1. **Activate Virtual Environment in terminal:**
   ```powershell
   cd "f:\Minor Project\backend"
   .\.venv\Scripts\Activate.ps1
   ```

2. **Verify Database Connection:**
   ```powershell
   python test_postgres.py
   ```

3. **Populate Database (If not already seeded):**
   ```powershell
   python seed_data.py
   ```

4. **Start Backend Server:**
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - **Interactive Mobile App UI (Instant Testing):** Open [http://localhost:8000/app](http://localhost:8000/app) in your browser.
   - **Interactive API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

### Part 2A: Instant Mobile App Testing (In Browser / Phone)
For testing right now without waiting to install Flutter SDK:
1. Simply make sure the backend is running.
2. Open **[http://localhost:8000/app](http://localhost:8000/app)** (or [http://localhost:8000/](http://localhost:8000/)) in Chrome or any browser.
3. You will see a complete, mobile-framed interactive interface with:
   - One-click demo logins for Student (`student@college.edu`) and Faculty (`faculty@college.edu`).
   - Personalized Notices matching student branch & CGPA.
   - Academic Resources with Branch & Semester filter.
   - Grounded RAG AI Chat Assistant with document citations.
   - Faculty PDF Uploads parsed by Gemini.

---

### Part 2B: Native Mobile App via Flutter (For Final Phone Build)
The complete Flutter Dart codebase is organized in `mobile_app/lib/`. When you install the Flutter SDK on Windows:
1. **Navigate to the `mobile_app` directory:**
   ```powershell
   cd "f:\Minor Project\mobile_app"
   ```

2. **Install Flutter Dependencies:**
   ```powershell
   flutter pub get
   ```

3. **Run on Chrome Web / Emulator / Device:**
   ```powershell
   # Run in Chrome browser for instant testing:
   flutter run -d chrome

   # Or run on connected Android phone / emulator:
   flutter run
   ```

> **Connecting Physical Phone via Wi-Fi:**
> In `mobile_app/lib/config/api_config.dart`, update `baseUrl` from `http://10.0.2.2:8000` to your computer's local Wi-Fi IP (e.g. `http://192.168.1.15:8000`).

---

## 👥 Demo Test Accounts

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Faculty Coordinator** | `faculty@college.edu` | `faculty123` | Can upload PDFs, create notices & manage resources |
| **Student (CSE 4th Year)** | `student@college.edu` | `student123` | CSE, 4th Year, 8.45 CGPA (Eligible for TCS placement) |
| **Student (ME 2nd Year)** | `me_student@college.edu` | `student123` | ME, 2nd Year, 7.20 CGPA (General sports notices only) |
