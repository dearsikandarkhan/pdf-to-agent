# backend/services/vector_service.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
import pickle
import os
import logging
from pathlib import Path

from config import get_settings
from models import ChunkMetadata, SearchResult

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    """Enhanced vector store service with multi-document support"""

    def __init__(self):
        self.vector_store_dir = Path(settings.VECTOR_STORE_DIR)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache: doc_id -> (index, chunks, metadata)
        self._cache: Dict[str, Tuple[faiss.Index, List[ChunkMetadata], Dict]] = {}
        
        logger.info(f"Initialized VectorStoreService at {self.vector_store_dir}")

    def store_document(
        self,
        doc_id: str,
        chunks: List[ChunkMetadata],
        embeddings: List[List[float]],
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Store document chunks and embeddings in FAISS index
        
        Args:
            doc_id: Unique document identifier
            chunks: List of chunk metadata
            embeddings: List of embedding vectors
            metadata: Optional document metadata
        """
        try:
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")

            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            dimension = embeddings_array.shape[1]

            # Create FAISS index
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)

            # Store in cache
            self._cache[doc_id] = (index, chunks, metadata or {})

            # Persist to disk
            self._save_to_disk(doc_id, index, chunks, metadata)

            logger.info(f"Stored document {doc_id}: {len(chunks)} chunks, dimension={dimension}")

        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            raise

    def search(
        self,
        doc_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search for similar chunks in a single document
        
        Args:
            doc_id: Document ID to search
            query_embedding: Query embedding vector
            top_k: Number of results to return
        
        Returns:
            List of SearchResult objects
        """
        try:
            # Load from cache or disk
            index, chunks, metadata = self._load_document(doc_id)

            # Convert query to numpy array
            query_array = np.array([query_embedding]).astype('float32')

            # Search
            distances, indices = index.search(query_array, min(top_k, len(chunks)))

            # Build results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(chunks):
                    chunk = chunks[idx]
                    results.append(SearchResult(
                        doc_id=doc_id,
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        score=float(1 / (1 + dist)),  # Convert distance to similarity score
                        page_num=chunk.page_num,
                        metadata={
                            "chunk_index": chunk.chunk_index,
                            "char_count": chunk.char_count,
                            "distance": float(dist)
                        }
                    ))

            logger.debug(f"Search in {doc_id}: found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed for document {doc_id}: {e}")
            raise

    def search_multi_documents(
        self,
        doc_ids: List[str],
        query_embedding: List[float],
        top_k_per_doc: int = 3,
        max_total_results: int = 10
    ) -> List[SearchResult]:
        """
        Search across multiple documents
        
        Args:
            doc_ids: List of document IDs to search
            query_embedding: Query embedding vector
            top_k_per_doc: Results per document
            max_total_results: Maximum total results to return
        
        Returns:
            List of SearchResult objects sorted by score
        """
        all_results = []

        for doc_id in doc_ids:
            try:
                results = self.search(doc_id, query_embedding, top_k_per_doc)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search document {doc_id}: {e}")
                continue

        # Sort by score (descending) and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:max_total_results]

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store
        
        Args:
            doc_id: Document ID to delete
        
        Returns:
            True if successful
        """
        try:
            # Remove from cache
            if doc_id in self._cache:
                del self._cache[doc_id]

            # Remove from disk
            file_path = self.vector_store_dir / f"{doc_id}.pkl"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted document {doc_id} from vector store")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def document_exists(self, doc_id: str) -> bool:
        """Check if document exists in vector store"""
        if doc_id in self._cache:
            return True
        file_path = self.vector_store_dir / f"{doc_id}.pkl"
        return file_path.exists()

    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stored document"""
        try:
            _, chunks, metadata = self._load_document(doc_id)
            return {
                "doc_id": doc_id,
                "chunk_count": len(chunks),
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Failed to get info for document {doc_id}: {e}")
            return None

    def _load_document(self, doc_id: str) -> Tuple[faiss.Index, List[ChunkMetadata], Dict]:
        """Load document from cache or disk"""
        # Check cache first
        if doc_id in self._cache:
            return self._cache[doc_id]

        # Load from disk
        file_path = self.vector_store_dir / f"{doc_id}.pkl"
        if not file_path.exists():
            raise FileNotFoundError(f"Document {doc_id} not found in vector store")

        with open(file_path, "rb") as f:
            data = pickle.load(f)
            index = data["index"]
            chunks = data["chunks"]
            metadata = data.get("metadata", {})

        # Add to cache
        self._cache[doc_id] = (index, chunks, metadata)
        
        return index, chunks, metadata

    def _save_to_disk(
        self,
        doc_id: str,
        index: faiss.Index,
        chunks: List[ChunkMetadata],
        metadata: Dict
    ) -> None:
        """Save document to disk"""
        file_path = self.vector_store_dir / f"{doc_id}.pkl"
        
        data = {
            "index": index,
            "chunks": chunks,
            "metadata": metadata
        }

        with open(file_path, "wb") as f:
            pickle.dump(data, f)

    def clear_cache(self) -> None:
        """Clear the in-memory cache"""
        self._cache.clear()
        logger.info("Vector store cache cleared")

    def get_cache_size(self) -> int:
        """Get number of documents in cache"""
        return len(self._cache)


# Global instance
_vector_service = None

def get_vector_service() -> VectorStoreService:
    """Get or create global vector service instance"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorStoreService()
    return _vector_service
