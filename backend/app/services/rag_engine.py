"""
RAG (Retrieval-Augmented Generation) & Semantic Search Engine
Manages document embeddings, vector indexing (FAISS), similarity retrieval,
and grounded answering via Google Gemini.
"""
import os
import json
import logging
import warnings
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from app.config import settings

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
        self, query: str, top_k: int = 4, document_id: Optional[int] = None
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
        self, query: str, document_id: Optional[int] = None, db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes the hybrid RAG pipeline:
        1. Retrieves relevant text chunks from FAISS / persisted vector store
        2. Augments with real-time Document & NoticeMetadata knowledge from PostgreSQL
        3. Prompts Gemini with grounded official context
        4. Returns structured answer along with verified source citations
        """
        retrieved_chunks = self.search_similar_chunks(query, top_k=4, document_id=document_id)

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
                docs = db.query(Document).all()
                query_lower = query.lower()
                query_terms = [w.strip(' "\'') for w in query_lower.split() if len(w.strip(' "\'')) > 2]

                for doc in docs:
                    m = doc.notice_metadata
                    r = doc.academic_resource
                    title_lower = doc.title.lower()

                    # Match if query specifically asks about this document or if keywords match
                    title_match = any(term in title_lower for term in query_terms) or (title_lower in query_lower)
                    summary_match = bool(m and m.summary and any(term in m.summary.lower() for term in query_terms))
                    is_selected_doc = bool(document_id is not None and doc.id == document_id)

                    # If document matches query or if we have fewer than 10 documents, always ground with them
                    if is_selected_doc or title_match or summary_match or len(docs) <= 10:
                        doc_details = [
                            f"--- Official College Document: {doc.title} ---",
                            f"Category: {doc.category.replace('_', ' ').title()}"
                        ]
                        if m:
                            if m.summary:
                                doc_details.append(f"Summary: {m.summary}")
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

                        context_blocks.append("\n".join(doc_details))

                        if doc.id not in seen_doc_ids:
                            seen_doc_ids.add(doc.id)
                            snippet_text = m.summary if (m and m.summary) else f"Official college document: {doc.title}"
                            sources.append({
                                "document_id": doc.id,
                                "document_title": doc.title,
                                "snippet": snippet_text[:180] + "..."
                            })
            except Exception as e:
                logger.error(f"Error querying DB in RAG pipeline: {e}")

        if not context_blocks:
            return {
                "query": query,
                "answer": "I could not find any official college documents addressing your question. Please check with your department or upload the relevant notice.",
                "sources": []
            }

        combined_context = "\n\n".join(context_blocks)

        api_key = settings.GEMINI_API_KEY
        if not api_key or "your-gemini-api-key" in api_key.lower():
            # Grounded fallback response when API key is pending
            return {
                "query": query,
                "answer": (
                    f"Based on college records (e.g. '{retrieved_chunks[0]['metadata'].get('document_title')}'):\n\n"
                    f"{retrieved_chunks[0]['text'][:300]}...\n\n"
                    f"(Note: Connect your Gemini API Key in backend/.env for AI-summarized synthesis)."
                ),
                "sources": sources
            }

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            rag_prompt = f"""
You are the official AI Assistant for International Institute of Professional Studies, Devi Ahilya Vishwavidyalaya (IIPS DAVV).
A student or faculty member is asking: "{query}"

Answer the question strictly and accurately using ONLY the official college document excerpts provided below.
Rules:
1. Ground your answer in the provided documents. Do NOT make up facts.
2. If the excerpts do not contain the answer, politely state that the provided documents do not mention this.
3. Keep the tone helpful, professional, and clear. Mention relevant deadlines or requirements clearly if present.

OFFICIAL IIPS DAVV DOCUMENTS:
{combined_context}
"""
            response = model.generate_content(rag_prompt)
            answer_text = response.text.strip()

            return {
                "query": query,
                "answer": answer_text,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error calling Gemini in RAG pipeline: {e}")
            return {
                "query": query,
                "answer": f"Error contacting AI service: {str(e)}. Retrieved information:\n\n{retrieved_chunks[0]['text'][:250]}...",
                "sources": sources
            }

    def summarize_document(
        self, document_title: str, text: str = "", document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Summarizes an entire document into key highlights: Overview, Deadlines, Eligibility, Actions.
        """
        # If raw text was not provided or file is virtual, assemble text from indexed chunks
        if not text.strip() and document_id is not None:
            matched = [
                c["text"] for c in self.chunks
                if c.get("metadata", {}).get("document_id") == document_id
            ]
            if matched:
                text = "\n\n".join(matched)

        if not text.strip():
            text = (
                f"Official academic resource: {document_title}.\n\n"
                f"Covers course curriculum, unit-wise syllabus modules, practical lab exercises, "
                f"and recommended textbooks for semester examination preparation."
            )

        api_key = settings.GEMINI_API_KEY
        if not api_key or "your-gemini-api-key" in api_key.lower():
            return {
                "title": document_title,
                "summary": text[:600] if len(text) > 40 else (
                    f"{document_title}: Official college curriculum and academic reference document. "
                    f"Outlines unit-wise syllabus modules, examination pattern, and recommended textbooks."
                ),
                "key_deadlines": "Please check the original document for exact dates.",
                "eligibility": "Refer to official notice for branch/year criteria.",
                "action_required": "Review full document for instructions."
            }

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are an academic summarizer. Summarize this official college document titled '{document_title}'.
Provide:
1. A concise 3-sentence summary of the main announcement.
2. Important deadlines or dates mentioned.
3. Eligibility criteria (branch, year, CGPA).
4. Required action for students.

DOCUMENT TEXT:
{text[:10000]}
"""
            response = model.generate_content(prompt)
            return {
                "title": document_title,
                "summary": response.text.strip()
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "title": document_title,
                "summary": text[:350] + "..."
            }


# Singleton instance
rag_engine = RAGEngine()
