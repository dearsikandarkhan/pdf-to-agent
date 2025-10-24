# backend/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import uuid

from config import settings
from models import (
    UploadResponse, QueryResponse,
    ComparisonResponse, DocumentListResponse, ErrorResponse, HealthCheck
)
from services.document_service import get_document_service
from services.query_service import get_query_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="Multi-document PDF RAG system with OpenAI and Ollama support"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get services
document_service = get_document_service()
query_service = get_query_service()


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.API_VERSION,
        services={
            "document_service": True,
            "query_service": True,
            "vector_service": True
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "upload": "/upload",
            "query": "/query",
            "compare": "/compare",
            "documents": "/documents/{session_id}",
            "health": "/health"
        }
    }


# ============================================================================
# Document Management Endpoints
# ============================================================================

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    embedding_provider: Optional[str] = Form(None)
):
    """
    Upload and process a PDF document

    - **file**: PDF file to upload
    - **session_id**: Session ID (generated if not provided)
    - **embedding_provider**: 'openai' or 'ollama' (default from config)
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        # Read file content
        content = await file.read()

        # Process document
        metadata = await document_service.upload_document(
            file_content=content,
            filename=file.filename,
            session_id=session_id,
            embedding_provider=embedding_provider
        )

        return UploadResponse(
            doc_id=metadata.doc_id,
            filename=metadata.filename,
            file_size=metadata.file_size,
            num_pages=metadata.num_pages,
            num_chunks=metadata.chunk_count,
            message="Document uploaded and processed successfully",
            upload_timestamp=metadata.upload_timestamp
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/documents/{session_id}", response_model=DocumentListResponse)
async def list_documents(session_id: str):
    """List all documents for a session"""
    try:
        documents = document_service.list_documents_by_session(session_id)

        return DocumentListResponse(
            session_id=session_id,
            documents=[
                {
                    "doc_id": doc.doc_id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "num_pages": doc.num_pages,
                    "chunk_count": doc.chunk_count,
                    "upload_timestamp": doc.upload_timestamp.isoformat(),
                    "embedding_provider": doc.embedding_provider
                }
                for doc in documents
            ],
            total_count=len(documents)
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, session_id: str = Form(...)):
    """Delete a document"""
    try:
        success = document_service.delete_document(doc_id, session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )

        return {"message": "Document deleted successfully", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# Query Endpoints
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def query_documents(
    question: str = Form(...),
    session_id: str = Form(...),
    doc_ids: Optional[str] = Form(None),  # Comma-separated list
    llm_provider: Optional[str] = Form("ollama"),
    top_k: int = Form(5)
):
    """
    Query documents with a question

    - **question**: Question to ask
    - **session_id**: Session ID
    - **doc_ids**: Optional comma-separated doc IDs (queries all if not provided)
    - **llm_provider**: 'openai' or 'ollama'
    - **top_k**: Number of chunks to retrieve
    """
    try:
        # Parse doc_ids if provided
        doc_id_list = None
        if doc_ids:
            doc_id_list = [d.strip() for d in doc_ids.split(',') if d.strip()]

        # Query documents
        result = await query_service.query_documents(
            question=question,
            session_id=session_id,
            doc_ids=doc_id_list,
            llm_provider=llm_provider,
            top_k=top_k,
            include_sources=True
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    question: str = Form(...),
    doc_ids: str = Form(...),  # Comma-separated list
    session_id: str = Form(...),
    llm_provider: Optional[str] = Form("ollama")
):
    """
    Compare how different documents answer the same question

    - **question**: Question to ask
    - **doc_ids**: Comma-separated list of document IDs (min 2, max 10)
    - **session_id**: Session ID
    - **llm_provider**: 'openai' or 'ollama'
    """
    try:
        # Parse doc_ids
        doc_id_list = [d.strip() for d in doc_ids.split(',') if d.strip()]

        if len(doc_id_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 documents required for comparison"
            )

        if len(doc_id_list) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 documents for comparison"
            )

        # Compare documents
        result = await query_service.compare_documents(
            question=question,
            doc_ids=doc_id_list,
            session_id=session_id,
            llm_provider=llm_provider
        )

        return ComparisonResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else None
        ).model_dump()
    )