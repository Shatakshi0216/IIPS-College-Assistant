"""
Pydantic Schemas for AI Chatbot, RAG Queries, and Document Summaries
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatQueryRequest(BaseModel):
    query: str = Field(..., example="What is the attendance requirement for mid-terms?")
    document_id: Optional[int] = Field(None, description="Optional: Limit RAG query to a specific document")


class SourceCitation(BaseModel):
    document_id: Optional[int] = None
    document_title: str
    snippet: str


class ChatQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation] = []


class DocumentSummaryResponse(BaseModel):
    document_id: int
    title: str
    summary: str
    key_deadlines: Optional[str] = None
    eligibility: Optional[str] = None
    action_required: Optional[str] = None
