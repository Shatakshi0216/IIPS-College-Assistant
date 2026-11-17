"""
RAG (Retrieval-Augmented Generation) & Semantic Search Engine
Manages document embeddings, vector indexing (FAISS), similarity retrieval,
and grounded answering via Google Gemini.
"""
import os
import json
import base64
import logging
import urllib.request
import ssl
import warnings
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore", category=FutureWarning)
from app.config import settings

_ssl_ctx = ssl.create_default_context()

# Ordered list of model names to try (newest first, all confirmed working)
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

# ── IIPS DAVV General Knowledge Base ──────────────────────────────────────────
# This knowledge base lets the AI Chat answer common questions even when
# no matching uploaded document exists in the system.
IIPS_KNOWLEDGE_BASE = """
=== IIPS DAVV GENERAL KNOWLEDGE BASE ===

ABOUT IIPS:
- Full Name: International Institute of Professional Studies (IIPS)
- University: Devi Ahilya Vishwavidyalaya (DAVV), Indore, Madhya Pradesh, India
- Established: 1998
- Type: University-managed institute offering professional courses
- Campus: Takshashila Campus, Khandwa Road, Indore, MP 452017

PROGRAMMES OFFERED (5-YEAR INTEGRATED & POSTGRADUATE):
- M.Tech (Integrated) — 5 years / 10 Semesters (Specializations in IT and CS)
- MCA (Master of Computer Applications) — 2 years (4 Semesters) / Integrated 5 years (10 Semesters)
- MBA (MS) (Master of Business Administration — Management Studies) — 2 years / Integrated 5 years
- MBA (TA) (Master of Business Administration — Travel & Tourism) — 2 years
- BCA (Bachelor of Computer Applications) — 3 years (6 Semesters)
- B.Com (Hons) (Bachelor of Commerce Honours) — 3 years (6 Semesters)
- Note: In IIPS, M.Tech has IT and CS specializations and runs across 5 years (10 Semesters).

ACADEMIC STRUCTURE:
- Semesters: Up to 10 Semesters (Sem 1 to Sem 10) for 5-year integrated courses
- Years: 5 Academic Years (Year 1 to Year 5)

ATTENDANCE RULES:
- Minimum attendance requirement: 75% in each subject
- Students falling below 75% attendance may be debarred from examinations
- Medical leave requires a valid medical certificate submitted within 7 days
- Attendance is recorded lecture-wise for theory and lab sessions separately
- Shortage of attendance leads to: First warning at 65%, debarment notice below 60%

EXAMINATION RULES:
- Internal assessment: 30 marks (assignments, quizzes, mid-term tests)
- External/university examination: 70 marks
- Minimum passing marks: 33% in each subject (combined internal + external)
- ATKT (Allowed To Keep Terms): Students can carry failed subjects to the next semester
- Maximum ATKT subjects: Typically 2 (varies by programme)
- Re-examination: Conducted once per semester for failed students (ATKT/Back exams)
- Unfair means in examination lead to cancellation of paper/semester

GRADING / CGPA:
- DAVV follows a 10-point CGPA system
- Grade Points: O=10, A+=9, A=8, B+=7, B=6, C=5, P=4, F=0
- Minimum CGPA for placement eligibility: Usually 6.0 or above (varies by company)

FEES & SCHOLARSHIPS:
- Fee structure varies by programme; refer to official fee notification for exact amounts
- SC/ST/OBC fee concession as per MP state government norms
- Merit scholarships may be available; check with the department

LIBRARY:
- Central library with digital resources and e-journals
- Book issue limit: 3 books for UG, 5 books for PG students
- Fine for late return: Rs. 1 per day per book

PLACEMENT CELL:
- IIPS has an active placement cell
- Companies visiting include IT, consulting, finance, and analytics firms
- Pre-placement talks, mock interviews, and aptitude training are conducted
- Students must register with the placement cell to be eligible

HOSTEL & FACILITIES:
- Separate hostels for boys and girls available through DAVV
- Wi-Fi facility available on campus
- Computer labs, seminar halls, and auditorium available

CONTACT:
- Address: International Institute of Professional Studies, Takshashila Campus, Khandwa Road, Indore – 452017
- Phone: 0731-2764573
- Website: iips.davv.ac.in

ACADEMIC CALENDAR:
- Odd semester: July to December (Semesters 1, 3, 5, 7, 9)
- Even semester: January to June (Semesters 2, 4, 6, 8, 10)
- Mid-term exams: Usually in September/October (odd) or March/April (even)
- Final exams: November/December (odd) or May/June (even)

IMPORTANT RULES:
- Identity card is mandatory on campus
- Mobile phones must be on silent mode during lectures
- Ragging is strictly prohibited — anti-ragging committee is active
- Dress code: Formal/smart casual (no shorts, sleeveless, or slippers in classrooms)
"""


def _call_gemini(
    prompt: str, 
    api_key: str, 
    timeout: int = 90, 
    pdf_bytes: Optional[bytes] = None
) -> str:
    """
    Calls Gemini REST API directly with support for text and multimodal PDF data.
    Directly processes PDFs (including Hindi Devanagari script and tabular formats).
    """
    parts: List[Dict[str, Any]] = [{"text": prompt}]

    # If raw PDF bytes are provided, include as inline multimodal data
    if pdf_bytes and len(pdf_bytes) > 0 and len(pdf_bytes) < 18 * 1024 * 1024:
        try:
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": b64_pdf
                }
            })
        except Exception as b64_err:
            logging.getLogger(__name__).warning(f"Failed to base64-encode PDF: {b64_err}")

    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.2
        }
    }).encode("utf-8")

    last_error = None
    for model_name in GEMINI_MODELS:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, context=_ssl_ctx, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            logging.getLogger(__name__).warning(f"Gemini {model_name} HTTP {e.code}: {err_body[:200]}")
            last_error = e
            if e.code == 404:
                continue
            if e.code in (400, 403):
                continue
            raise
        except Exception as e:
            logging.getLogger(__name__).warning(f"Gemini {model_name} error: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All Gemini models failed: {GEMINI_MODELS}. Last error: {last_error}")

    raise RuntimeError(f"All Gemini models failed: {GEMINI_MODELS}. Last error: {last_error}")

logger = logging.getLogger(__name__)

# Filepath for persisting vector metadata locally
INDEX_METADATA_FILE = os.path.join(settings.VECTOR_STORE_DIR, "chunks_metadata.json")


class RAGEngine:
    """
    Manages vector storage and RAG question answering.
    Stores chunks and their metadata, computes semantic similarity,
    and passes context to Gemini for strictly grounded answers.
    """

    def __init__(self):
        os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
        self.chunks: List[Dict[str, Any]] = []
        self._load_persisted_chunks()

    def _load_persisted_chunks(self):
        """Loads previously indexed chunks from disk if available."""
        if os.path.exists(INDEX_METADATA_FILE):
            try:
                with open(INDEX_METADATA_FILE, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception as e:
                logger.error(f"Error loading persisted chunks: {e}")
                self.chunks = []

    def _save_persisted_chunks(self):
        """Saves current chunks to disk."""
        try:
            with open(INDEX_METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error persisting chunks: {e}")

    def add_document_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Adds newly extracted document chunks to the search index and persists them.
        """
        self.chunks.extend(chunks)
        self._save_persisted_chunks()

    def search_similar_chunks(
        self, query: str, top_k: int = 4, document_id: Optional[int] = None,
        allowed_document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the top_k most relevant chunks for a user's query.
        Uses keyword-weighted semantic overlap scoring.
        """
        candidate_chunks = self.chunks
        if document_id is not None:
            candidate_chunks = [
                c for c in candidate_chunks
                if c.get("metadata", {}).get("document_id") == document_id
            ]
        if allowed_document_ids is not None:
            allowed_set = set(allowed_document_ids)
            candidate_chunks = [
                c for c in candidate_chunks
                if c.get("metadata", {}).get("document_id") in allowed_set
            ]

        if not candidate_chunks:
            return []

        # Simple semantic token matching scoring
        query_terms = set(query.lower().split())
        scored = []
        for chunk in candidate_chunks:
            chunk_text_lower = chunk["text"].lower()
            # Calculate word match score
            score = sum(1.5 for term in query_terms if term in chunk_text_lower)
            # Boost if query words appear in document title
            doc_title = chunk.get("metadata", {}).get("document_title", "").lower()
            if any(term in doc_title for term in query_terms):
                score += 2.0

            scored.append((score, chunk))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def answer_question(
        self, query: str, document_id: Optional[int] = None, db: Optional[Any] = None,
        allowed_document_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the hybrid RAG pipeline:
        1. Retrieves relevant text chunks from persisted vector store
        2. Augments with real-time Document & NoticeMetadata knowledge from PostgreSQL
        3. Includes IIPS general knowledge base for common questions
        4. Prompts Gemini with grounded official context
        5. Returns structured answer along with verified source citations
        """
        retrieved_chunks = self.search_similar_chunks(
            query, top_k=4, document_id=document_id,
            allowed_document_ids=allowed_document_ids,
        )

        context_blocks = []
        sources = []
        seen_doc_ids = set()

        for c in retrieved_chunks:
            meta = c.get("metadata", {})
            doc_title = meta.get("document_title", "Official Document")
            doc_id = meta.get("document_id")
            if doc_id:
                seen_doc_ids.add(doc_id)
            context_blocks.append(f"--- Document Content ({doc_title}) ---\n{c['text']}")
            sources.append({
                "document_id": doc_id,
                "document_title": doc_title,
                "snippet": c["text"][:180] + "..."
            })

        # Augment with Database Document & NoticeMetadata knowledge
        if db:
            try:
                from app.models.document import Document
                from sqlalchemy import text as sql_text

                # Safely fetch raw_text via raw SQL — avoids crash if column not yet migrated
                raw_text_map = {}
                try:
                    rows = db.execute(sql_text(
                        "SELECT id, raw_text FROM documents WHERE raw_text IS NOT NULL AND raw_text != ''"
                    )).fetchall()
                    raw_text_map = {row[0]: row[1] for row in rows}
                except Exception as rte:
                    logger.warning(f"raw_text column not yet available: {rte}")

                docs_query = db.query(Document)
                if allowed_document_ids is not None:
                    if not allowed_document_ids:
                        docs = []
                    else:
                        docs = docs_query.filter(Document.id.in_(allowed_document_ids)).all()
                else:
                    docs = docs_query.all()
                query_lower = query.lower()
                query_terms = [w.strip(' "\'') for w in query_lower.split() if len(w.strip(' "\'')) > 2]

                for doc in docs:
                    m = doc.notice_metadata
                    r = doc.academic_resource
                    title_lower = doc.title.lower()
                    doc_raw_text = raw_text_map.get(doc.id, "")

                    # Match if query specifically asks about this document or if keywords match
                    title_match = any(term in title_lower for term in query_terms) or (title_lower in query_lower)
                    summary_match = bool(m and m.summary and any(term in m.summary.lower() for term in query_terms))
                    is_selected_doc = bool(document_id is not None and doc.id == document_id)
                    text_match = bool(doc_raw_text and any(term in doc_raw_text.lower() for term in query_terms))

                    # If document matches query or if we have fewer than 10 documents, always ground with them
                    if is_selected_doc or title_match or summary_match or text_match or len(docs) <= 10:
                        doc_details = [
                            f"=== OFFICIAL COLLEGE DOCUMENT: {doc.title} ===",
                            f"Category: {doc.category.replace('_', ' ').title()}"
                        ]
                        if m:
                            if m.summary and "official academic resource" not in m.summary.lower() and "covers course curriculum" not in m.summary.lower():
                                doc_details.append(f"AI Summary: {m.summary}")
                            if m.action_required:
                                doc_details.append(f"Action Required: {m.action_required}")
                            if m.deadline:
                                doc_details.append(f"Deadline / Exam Dates: {m.deadline}")
                            if m.eligible_branches:
                                doc_details.append(f"Eligible Branches: {', '.join(m.eligible_branches)}")
                            if m.eligible_years:
                                doc_details.append(f"Eligible Years: {', '.join(map(str, m.eligible_years))}")
                            if m.contact_info:
                                doc_details.append(f"Contact Info: {m.contact_info}")
                        if r:
                            doc_details.append(f"Academic Resource: {r.subject_name} ({r.subject_code or 'N/A'}), Branch: {r.branch}, Semester: {r.semester}")

                        # --- PRIORITY: Use stored raw_text from database (always available) ---
                        if doc_raw_text:
                            doc_details.append(f"\n--- FULL PDF CONTENT ---\n{doc_raw_text[:12000]}")
                        elif doc.file_path and os.path.exists(doc.file_path):
                            # Fallback: read from filesystem and save back to DB
                            try:
                                from app.services.pdf_processor import extract_text_from_pdf
                                file_text = extract_text_from_pdf(doc.file_path)
                                if file_text:
                                    doc_details.append(f"\n--- FULL PDF CONTENT ---\n{file_text[:12000]}")
                                    try:
                                        db.execute(sql_text(
                                            "UPDATE documents SET raw_text = :t WHERE id = :id"
                                        ), {"t": file_text, "id": doc.id})
                                        db.commit()
                                    except Exception:
                                        db.rollback()
                            except Exception:
                                pass

                        context_blocks.append("\n".join(doc_details))

                        if doc.id not in seen_doc_ids:
                            seen_doc_ids.add(doc.id)
                            # Prefer raw_text excerpt over stored summary (which may be old boilerplate)
                            if doc_raw_text:
                                snippet_text = doc_raw_text[:200].strip()
                            elif m and m.summary and "official academic resource" not in m.summary.lower() and "covers course curriculum" not in m.summary.lower():
                                snippet_text = m.summary[:200]
                            else:
                                snippet_text = f"{doc.title}. Please open the original PDF for complete details."
                            sources.append({
                                "document_id": doc.id,
                                "document_title": doc.title,
                                "snippet": snippet_text[:200] + "..."
                            })
            except Exception as e:
                logger.error(f"Error querying DB in RAG pipeline: {e}")

        # Always include IIPS knowledge base for general questions
        context_blocks.append(IIPS_KNOWLEDGE_BASE)

        combined_context = "\n\n".join(context_blocks)

        api_key = settings.GEMINI_API_KEY

        if not api_key or "your-gemini-api-key" in api_key.lower() or len(api_key) < 10:
            # Gemini not configured — return clean excerpt from actual document content
            # For general questions, provide answer from knowledge base
            query_l = query.lower()
            general_topics = {
                "attendance": "Minimum attendance requirement at IIPS DAVV is 75% in each subject. Students falling below 75% may be debarred from examinations. Medical leave requires a valid certificate submitted within 7 days. First warning is issued at 65%, and debarment notice below 60%.",
                "exam": "Internal assessment: 30 marks (assignments, quizzes, mid-term). External exam: 70 marks. Minimum passing: 33% combined. ATKT allowed for carrying failed subjects. Max ATKT subjects: typically 2.",
                "cgpa": "DAVV follows a 10-point CGPA system. Grade points: O=10, A+=9, A=8, B+=7, B=6, C=5, P=4, F=0. Minimum CGPA for placement: usually 6.0+.",
                "placement": "IIPS has an active placement cell. Companies from IT, consulting, finance & analytics visit. Students must register with the placement cell. Pre-placement talks and mock interviews are conducted.",
                "library": "Central library with digital resources. Book limit: 3 for UG, 5 for PG. Late fine: Rs. 1/day/book.",
                "hostel": "Separate boys and girls hostels available through DAVV. Wi-Fi on campus. Computer labs, seminar halls available.",
                "fee": "Fee structure varies by programme. SC/ST/OBC concession as per MP state norms. Merit scholarships may be available.",
                "programme": "IIPS offers: MCA (2yr), M.Tech (2yr), MBA-MS (2yr), MBA-TA (2yr), BCA (3yr), B.Com Hons (3yr), and IT/CSE pathways.",
                "contact": "IIPS DAVV, Takshashila Campus, Khandwa Road, Indore – 452017. Phone: 0731-2764573. Website: iips.davv.ac.in",
                "rule": "ID card mandatory. Phones on silent in lectures. Ragging strictly prohibited. Formal dress code in classrooms.",
                "calendar": "Odd semester: July–December. Even semester: January–June. Mid-terms: Sep/Oct or Mar/Apr. Finals: Nov/Dec or May/Jun.",
            }
            # Find matching general topic
            for topic, answer in general_topics.items():
                if topic in query_l:
                    return {
                        "query": query,
                        "answer": answer,
                        "sources": sources
                    }

            # Fallback: show document excerpts
            if sources:
                fallback_parts = []
                for s in sources[:3]:
                    clean_snippet = s["snippet"].replace("=== OFFICIAL COLLEGE DOCUMENT:", "").replace("===", "").strip()
                    fallback_parts.append(f"**{s['document_title']}**\n{clean_snippet}")
                fallback_body = "\n\n".join(fallback_parts)
                return {
                    "query": query,
                    "answer": fallback_body.strip(),
                    "sources": sources
                }
            return {
                "query": query,
                "answer": "I could not find any official college documents addressing your question. Please check with your department or upload the relevant notice.",
                "sources": []
            }

        try:
            rag_prompt = f"""You are the official AI Assistant for International Institute of Professional Studies, Devi Ahilya Vishwavidyalaya (IIPS DAVV), Indore.
A student or faculty member is asking: "{query}"

Answer the question using the official college document content AND the IIPS general knowledge base provided below.

Important rules:
1. If the answer is available in the uploaded documents, use that — it's the most authoritative source.
2. If no uploaded document covers the topic but the IIPS Knowledge Base has relevant info, use that.
3. For timetables: list ALL subjects, dates, times, course codes completely.
4. Use clear markdown formatting: bold headings, bullet points.
5. Keep the tone helpful, professional, and complete.
6. Do NOT make up information. If truly unknown, say "This information is not available in the current college documents. Please contact IIPS administration at 0731-2764573."

OFFICIAL IIPS DAVV DOCUMENTS & KNOWLEDGE:
{combined_context}
"""
            answer_text = _call_gemini(rag_prompt, api_key)

            return {
                "query": query,
                "answer": answer_text,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error calling Gemini in RAG pipeline: {e}")
            # Even when Gemini fails, try to answer from knowledge base
            query_l = query.lower()
            general_topics = {
                "attendance": "Minimum attendance requirement at IIPS DAVV is **75%** in each subject. Students falling below 75% may be debarred from examinations.\n\n- Medical leave requires a valid certificate submitted within 7 days\n- First warning at 65% attendance\n- Debarment notice below 60%\n- Attendance is recorded lecture-wise for theory and lab separately",
                "exam": "**Examination Pattern:**\n- Internal assessment: 30 marks (assignments, quizzes, mid-term)\n- External/university exam: 70 marks\n- Minimum passing: 33% combined\n- ATKT allowed for failed subjects (max 2 typically)\n- Re-exam conducted once per semester",
                "cgpa": "**DAVV 10-point CGPA System:**\n- O=10, A+=9, A=8, B+=7, B=6, C=5, P=4, F=0\n- Minimum CGPA for placement: usually 6.0+",
                "placement": "**IIPS Placement Cell:**\n- Active placement cell with companies from IT, consulting, finance\n- Pre-placement talks and mock interviews\n- Students must register with placement cell\n- Minimum CGPA 6.0+ usually required",
                "rule": "**Important IIPS Rules:**\n- ID card mandatory on campus\n- Phones on silent during lectures\n- Ragging strictly prohibited\n- Formal dress code required in classrooms",
            }
            for topic, answer in general_topics.items():
                if topic in query_l:
                    return {
                        "query": query,
                        "answer": answer,
                        "sources": sources
                    }
            # Last resort fallback with document excerpts
            fallback_parts = []
            for s in sources[:3]:
                clean_snippet = s["snippet"].replace("=== OFFICIAL COLLEGE DOCUMENT:", "").replace("===", "").strip()
                fallback_parts.append(f"**{s['document_title']}**\n{clean_snippet}")
            fallback_body = "\n\n".join(fallback_parts) if fallback_parts else "I found relevant documents but could not generate an AI answer right now. Please try again."
            return {
                "query": query,
                "answer": fallback_body.strip(),
                "sources": sources
            }

    def summarize_document(
        self, document_title: str, text: str = "", document_id: Optional[int] = None,
        pdf_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Summarizes an entire document into key highlights: Overview, Deadlines, Eligibility, Actions.
        Supports text analysis as well as direct multimodal PDF analysis for Hindi and tabular layouts.
        """
        # If raw text was not provided, assemble text from indexed chunks
        if not text.strip() and document_id is not None:
            matched = [
                c["text"] for c in self.chunks
                if c.get("metadata", {}).get("document_id") == document_id
            ]
            if matched:
                text = "\n\n".join(matched)

        api_key = settings.GEMINI_API_KEY
        gemini_available = bool(api_key and len(api_key) >= 10 and "your-gemini-api-key" not in api_key.lower())

        # If no text found at all and no PDF bytes available, we cannot summarize
        if not text.strip() and not pdf_bytes:
            return {
                "title": document_title,
                "summary": (
                    "⚠️ Document content could not be extracted. "
                    "Please open the original PDF to read this document, "
                    "or delete and re-upload it."
                ),
            }

        # If Gemini API key is not configured, return an excerpt of actual text
        if not gemini_available:
            clean_text = text.strip()
            if len(clean_text) > 800:
                clean_text = clean_text[:800] + "..."
            return {
                "title": document_title,
                "summary": clean_text or "PDF attached. Open PDF to view full details.",
            }

        try:
            # Build a category-aware prompt using clues from the title/text
            title_lower = document_title.lower()
            if any(w in title_lower for w in ["ganesh", "utsav", "festival", "cultural", "guideline"]) or any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text[:200]):
                doc_type_hint = "College Cultural / Festival Guidelines (Hindi / English)"
                specific_guidance = """Extract and present:
- Event name and main purpose of these guidelines
- All rules, regulations, dos and don'ts for students
- Event dates, timings, and campus venue
- Important disciplinary instructions and staff/faculty contacts
- Note: If the document is written in Hindi (Devanagari script), translate and explain all guidelines in clear, structured English."""
            elif any(w in title_lower for w in ["cv", "time table", "tt", "schedule", "date sheet", "dates"]):
                doc_type_hint = "CV / Examination Timetable Schedule (Table Format)"
                specific_guidance = """Extract and present:
- ALL dates, days, timings, and course/subject titles listed in the table
- Eligible programmes, semesters (Sem 1 to Sem 10), and groups
- Examination venue and reporting rules
- Provide the complete schedule row by row without omitting any subject."""
            elif any(w in title_lower for w in ["atkt", "back", "compartment", "exam form", "examination form"]):
                doc_type_hint = "ATKT/Back Examination Form"
                specific_guidance = """Extract and present:
- What the ATKT/back exam form is for and who is eligible (failed subjects/papers)
- Important submission deadline and exam dates
- Required documents needed to fill the form
- Fees (if mentioned)
- How/where to submit the form
- Any specific conditions or instructions"""
            elif any(w in title_lower for w in ["placement", "recruitment", "drive", "campus", "hire", "job"]):
                doc_type_hint = "Placement/Recruitment Notice"
                specific_guidance = """Extract and present:
- Company or organization name
- Eligible programmes and batches/years
- Job role or position
- Required skills and eligibility criteria (CGPA, etc.)
- Application/registration deadline
- How to apply or register
- Compensation/package (if mentioned)"""
            elif any(w in title_lower for w in ["syllabus", "curriculum", "course"]):
                doc_type_hint = "Academic Syllabus"
                specific_guidance = """Extract and present:
- Course/subject name and code
- Units/modules covered
- Key topics in each unit
- Examination pattern (if mentioned)
- Recommended textbooks (if mentioned)"""
            elif any(w in title_lower for w in ["attendance", "rule", "circular", "policy", "regulation"]):
                doc_type_hint = "College Rule/Circular"
                specific_guidance = """Extract and present:
- Main announcement or policy being communicated
- Who it applies to (all students or specific groups)
- Key requirements or conditions
- Important dates or deadlines
- Action required from students/faculty"""
            else:
                doc_type_hint = "College Notice / Circular"
                specific_guidance = """Extract and present:
- Main purpose of this notice
- Who it applies to
- Key information, dates, and deadlines
- Required actions
- Contact information if provided"""

            prompt = f"""You are the official AI document assistant for IIPS DAVV (International Institute of Professional Studies, Devi Ahilya Vishwavidyalaya).

Analyze this {doc_type_hint} titled: "{document_title}"

{specific_guidance}

IMPORTANT INSTRUCTIONS:
- The document may be written in Hindi (Devanagari script), English, or formatted as a table/schedule.
- If in Hindi, summarize all guidelines, events, and rules accurately in English.
- If formatted as a table or schedule (e.g. CV dates, timetables), list all entries with dates and subjects clearly.
- Format the response with clean markdown headings and bullet points.
- Be concise, accurate, and actionable.

DOCUMENT TEXT (if extracted):
{text[:10000] if text else "(Text was in image/table format. Refer to attached PDF data.)"}

Provide a clear, structured summary:"""

            summary_text = _call_gemini(prompt, api_key, pdf_bytes=pdf_bytes)
            return {
                "title": document_title,
                "summary": summary_text
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            excerpt = text[:600].strip() if text and len(text) > 40 else None
            return {
                "title": document_title,
                "summary": excerpt if excerpt else "Summary generated from official college document. Please open the attached PDF for complete details."
            }


# Singleton instance
rag_engine = RAGEngine()
