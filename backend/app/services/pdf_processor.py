"""
==============================================================================
FILE: backend/app/services/pdf_processor.py
PURPOSE: PDF Processing Service.
         Extracts raw text and table layouts (bilingual Hindi/English)
         from uploaded PDF files and splits into chunks for RAG indexing.
==============================================================================
"""

import os
import logging
from io import BytesIO
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text and structured tables directly from PDF bytes.
    Uses pdfplumber (superior for Hindi Devanagari script, layout, and tables)
    with seamless fallback to pypdf.
    """
    if not pdf_bytes:
        return ""

    text_content = []

    # 1. Try pdfplumber first (handles tables, layout, and Unicode/Hindi significantly better)
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_parts = []
                # Extract text
                ptxt = page.extract_text(layout=False)
                if ptxt and ptxt.strip():
                    page_parts.append(ptxt.strip())
                # Extract tables (e.g. CV dates, timetables, examination schedules)
                try:
                    tables = page.extract_tables()
                    if tables:
                        for tbl in tables:
                            table_lines = []
                            for row in tbl:
                                if any(row):
                                    row_str = " | ".join(str(cell or "").strip() for cell in row)
                                    table_lines.append(row_str)
                            if table_lines:
                                page_parts.append("\n[TABLE DATA]:\n" + "\n".join(table_lines))
                except Exception:
                    pass

                if page_parts:
                    text_content.append("\n".join(page_parts))
    except Exception as exc:
        logger.warning(f"pdfplumber extraction note: {exc}")

    # 2. If pdfplumber didn't extract enough text, fallback/supplement with pypdf
    if not text_content or len("\n\n".join(text_content).strip()) < 50:
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            pypdf_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pypdf_parts.append(page_text.strip())
            if len("\n\n".join(pypdf_parts).strip()) > len("\n\n".join(text_content).strip()):
                return "\n\n".join(pypdf_parts)
        except Exception:
            pass

    return "\n\n".join(text_content)


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file on disk using extract_text_from_pdf_bytes."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")

    with open(file_path, "rb") as f:
        return extract_text_from_pdf_bytes(f.read())


def chunk_document_text(
    text: str,
    document_id: int,
    document_title: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict[str, Any]]:
    """Splits long extracted document text into overlapping chunks for RAG indexing."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    raw_chunks = splitter.split_text(text)
    processed_chunks = []

    for idx, chunk_str in enumerate(raw_chunks):
        processed_chunks.append({
            "text": chunk_str,
            "metadata": {
                "document_id": document_id,
                "document_title": document_title,
                "chunk_index": idx
            }
        })

    return processed_chunks
