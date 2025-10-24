# backend/services/document_service.py
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
from pathlib import Path
import logging

from config import get_settings
from models import DocumentMetadata, ChunkMetadata
from utils.pdf_parser import parse_pdf_content, validate_pdf_content
from utils.chunking import chunk_document
from services.embedding_service import get_embedding_service
from services.vector_service import get_vector_service

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """Service for managing document lifecycle"""

    def __init__(self):
        self.documents_dir = Path(settings.DOCUMENTS_DIR)
        self.metadata_dir = Path(settings.METADATA_DIR)
        
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.vector_service = get_vector_service()
        
        logger.info("Initialized DocumentService")

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        session_id: str,
        embedding_provider: str = None
    ) -> DocumentMetadata:
        """
        Upload and process a PDF document
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            session_id: User session ID
            embedding_provider: Which embedding service to use
        
        Returns:
            DocumentMetadata object
        """
        try:
            # Validate file size
            file_size = len(file_content)
            max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size:
                raise ValueError(f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)")

            # Validate PDF
            is_valid, error_msg = validate_pdf_content(file_content)
            if not is_valid:
                raise ValueError(f"Invalid PDF: {error_msg}")

            # Generate document ID
            doc_id = str(uuid.uuid4())

            # Parse PDF
            text, pdf_metadata = parse_pdf_content(file_content, filename)

            # Save original PDF
            pdf_path = self.documents_dir / f"{doc_id}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(file_content)

            # Chunk the document
            chunks = chunk_document(
                text=text,
                doc_id=doc_id,
                page_nums=pdf_metadata.get("page_numbers")
            )

            # Generate embeddings
            embedding_service = get_embedding_service(embedding_provider)
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = embedding_service.embed_documents(chunk_texts)

            # Store in vector store
            self.vector_service.store_document(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata=pdf_metadata
            )

            # Create metadata
            doc_metadata = DocumentMetadata(
                doc_id=doc_id,
                session_id=session_id,
                filename=filename,
                file_size=file_size,
                num_pages=pdf_metadata["num_pages"],
                upload_timestamp=datetime.now(),
                chunk_count=len(chunks),
                embedding_provider=embedding_provider or settings.DEFAULT_EMBEDDING_PROVIDER.value,
                metadata=pdf_metadata
            )

            # Save metadata
            self._save_metadata(doc_metadata)

            logger.info(
                f"Uploaded document {doc_id} ({filename}): "
                f"{pdf_metadata['num_pages']} pages, {len(chunks)} chunks"
            )

            return doc_metadata

        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {e}")
            raise

    def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document"""
        try:
            metadata_path = self.metadata_dir / f"{doc_id}.json"
            if not metadata_path.exists():
                return None

            with open(metadata_path, "r") as f:
                data = json.load(f)
                return DocumentMetadata(**data)

        except Exception as e:
            logger.error(f"Failed to get metadata for {doc_id}: {e}")
            return None

    def list_documents_by_session(self, session_id: str) -> List[DocumentMetadata]:
        """List all documents for a session"""
        documents = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    data = json.load(f)
                    if data.get("session_id") == session_id:
                        documents.append(DocumentMetadata(**data))
            except Exception as e:
                logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
                continue

        # Sort by upload timestamp (newest first)
        documents.sort(key=lambda x: x.upload_timestamp, reverse=True)
        
        logger.debug(f"Found {len(documents)} documents for session {session_id}")
        return documents

    def delete_document(self, doc_id: str, session_id: str) -> bool:
        """
        Delete a document
        
        Args:
            doc_id: Document ID
            session_id: Session ID (for authorization)
        
        Returns:
            True if successful
        """
        try:
            # Verify ownership
            metadata = self.get_document_metadata(doc_id)
            if not metadata:
                logger.warning(f"Document {doc_id} not found")
                return False

            if metadata.session_id != session_id:
                logger.warning(f"Session {session_id} not authorized to delete {doc_id}")
                return False

            # Delete from vector store
            self.vector_service.delete_document(doc_id)

            # Delete PDF file
            pdf_path = self.documents_dir / f"{doc_id}.pdf"
            if pdf_path.exists():
                pdf_path.unlink()

            # Delete metadata
            metadata_path = self.metadata_dir / f"{doc_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Deleted document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def get_document_count_by_session(self, session_id: str) -> int:
        """Get count of documents in a session"""
        return len(self.list_documents_by_session(session_id))

    def _save_metadata(self, metadata: DocumentMetadata) -> None:
        """Save document metadata to disk"""
        metadata_path = self.metadata_dir / f"{metadata.doc_id}.json"
        
        with open(metadata_path, "w") as f:
            json.dump(metadata.model_dump(mode='json'), f, indent=2, default=str)


# Global instance
_document_service = None

def get_document_service() -> DocumentService:
    """Get or create global document service instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
