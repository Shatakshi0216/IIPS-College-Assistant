"""
==============================================================================
FILE: backend/app/services/pdf_processor.py
PURPOSE: PDF Processing Service.
         Extracts raw text from uploaded PDF files and splits the text into
         manageable, overlapping chunks for AI embedding and RAG search.
==============================================================================
HOW IT WORKS:
1. extract_text_from_pdf():
   - Uses PyPDF's PdfReader to open the file.
   - Iterates through each page in sequence.
   - Extracts all plain text lines and joins them with clean spacing.
   
2. chunk_document_text():
   - Uses LangChain's RecursiveCharacterTextSplitter.
   - Cuts lengthy documents into chunks (default: 800 characters).
   - Keeps an overlap (default: 150 characters) so sentences sliced across
     boundaries don't lose context.
   - Attaches metadata (document_id, document_title, chunk_index) to each chunk
     so the AI can accurately cite sources.
==============================================================================
"""

import os
from typing import List, Dict, Any
from pypdf import PdfReader

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text content from a PDF document stored on disk.
    
    Args:
        file_path (str): Absolute or relative path to the .pdf file.
        
    Returns:
        str: Consolidated plain-text string extracted across all pages.
        
    Raises:
        FileNotFoundError: If the specified file_path does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")

    text_content = []
    reader = PdfReader(file_path)
    
    for page_idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_content.append(page_text.strip())

    return "\n\n".join(text_content)


def chunk_document_text(
    text: str,
    document_id: int,
    document_title: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Splits long extracted document text into overlapping chunks for RAG indexing.
    
    Why Chunking and Overlap Matter:
    - LLMs have context limits and perform best when fed specific, relevant paragraphs.
    - Chunk overlap (150 chars) ensures that if a vital rule (e.g., '75% attendance
      required for mid-terms') falls across two chunks, the meaning isn't severed.
      
    Args:
        text (str): Full text extracted from the PDF.
        document_id (int): Foreign key ID of the parent document.
        document_title (str): Title of the document for source citation.
        chunk_size (int): Max character length per chunk (default 800).
        chunk_overlap (int): Number of overlapping characters between chunks (default 150).
        
    Returns:
        List[Dict[str, Any]]: List of dictionary items with 'text' and 'metadata'.
    """
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
