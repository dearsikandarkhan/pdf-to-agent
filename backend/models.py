# backend/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# ============================================================================
# Request Models
# ============================================================================

class UploadRequest(BaseModel):
    """Request model for PDF upload"""
    session_id: Optional[str] = None

class QueryRequest(BaseModel):
    """Request model for querying documents"""
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)
    doc_ids: Optional[List[str]] = None  # If None, search all docs in session
    llm_provider: Literal["openai", "ollama"] = "ollama"
    top_k: int = Field(default=5, ge=1, le=20)
    include_sources: bool = True

    @validator('question')
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

class ComparisonRequest(BaseModel):
    """Request model for comparing answers across multiple documents"""
    question: str = Field(..., min_length=1, max_length=2000)
    doc_ids: List[str] = Field(..., min_items=2, max_items=10)
    session_id: str = Field(..., min_length=1)
    llm_provider: Literal["openai", "ollama"] = "ollama"

class DeleteDocumentRequest(BaseModel):
    """Request model for deleting a document"""
    doc_id: str
    session_id: str

# ============================================================================
# Response Models
# ============================================================================

class UploadResponse(BaseModel):
    """Response model for successful upload"""
    doc_id: str
    filename: str
    file_size: int
    num_pages: int
    num_chunks: int
    message: str
    upload_timestamp: datetime

class QueryResponse(BaseModel):
    """Response model for document query"""
    answer: str
    sources: List[Dict[str, Any]]
    doc_ids_used: List[str]
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ComparisonResponse(BaseModel):
    """Response model for document comparison"""
    question: str
    comparisons: List[Dict[str, Any]]  # One per document
    summary: str
    processing_time_ms: float

class DocumentListResponse(BaseModel):
    """Response model for listing documents in a session"""
    session_id: str
    documents: List[Dict[str, Any]]
    total_count: int

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# Data Models
# ============================================================================

class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document"""
    doc_id: str
    session_id: str
    filename: str
    file_size: int
    num_pages: int
    upload_timestamp: datetime
    chunk_count: int
    embedding_provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChunkMetadata(BaseModel):
    """Metadata for a document chunk"""
    chunk_id: str
    doc_id: str
    page_num: Optional[int] = None
    chunk_index: int
    text: str
    char_count: int
    token_count: Optional[int] = None

class SearchResult(BaseModel):
    """Individual search result from vector store"""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    page_num: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationHistory(BaseModel):
    """Conversation history for a session"""
    session_id: str
    doc_id: Optional[str] = None
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# Health Check Models
# ============================================================================

class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    services: Dict[str, bool] = Field(default_factory=dict)