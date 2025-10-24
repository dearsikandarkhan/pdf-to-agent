# backend/services/query_service.py
from typing import List, Dict, Any, Optional
import time
import logging

from config import get_settings
from models import SearchResult, QueryRequest, ComparisonRequest, ConversationMessage
from services.embedding_service import get_embedding_service
from services.llm_service import get_llm_service
from services.vector_service import get_vector_service
from services.document_service import get_document_service

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryService:
    """Service for handling document queries and comparisons"""

    def __init__(self):
        self.vector_service = get_vector_service()
        self.document_service = get_document_service()
        logger.info("Initialized QueryService")

    async def query_documents(
        self,
        question: str,
        session_id: str,
        doc_ids: Optional[List[str]] = None,
        llm_provider: str = None,
        top_k: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Query one or more documents
        
        Args:
            question: User's question
            session_id: Session ID
            doc_ids: List of document IDs (None = all docs in session)
            llm_provider: Which LLM to use
            top_k: Number of chunks to retrieve
            include_sources: Include source citations
        
        Returns:
            Dict with answer, sources, and metadata
        """
        start_time = time.time()

        try:
            # Get document IDs for this session
            if doc_ids is None:
                all_docs = self.document_service.list_documents_by_session(session_id)
                doc_ids = [doc.doc_id for doc in all_docs]

            if not doc_ids:
                return {
                    "answer": "No documents found in this session. Please upload a PDF first.",
                    "sources": [],
                    "doc_ids_used": [],
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "metadata": {"error": "no_documents"}
                }

            # Get embedding provider from first document
            first_doc_meta = self.document_service.get_document_metadata(doc_ids[0])
            embedding_provider = first_doc_meta.embedding_provider if first_doc_meta else None

            # Embed the question
            embedding_service = get_embedding_service(embedding_provider)
            query_embedding = embedding_service.embed_query(question)

            # Search across documents
            search_results = self.vector_service.search_multi_documents(
                doc_ids=doc_ids,
                query_embedding=query_embedding,
                top_k_per_doc=settings.TOP_K_PER_DOCUMENT,
                max_total_results=top_k
            )

            if not search_results:
                return {
                    "answer": "No relevant information found in the documents.",
                    "sources": [],
                    "doc_ids_used": doc_ids,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "metadata": {"error": "no_results"}
                }

            # Build context from search results
            context = self._build_context(search_results)

            # Generate answer
            llm_service = get_llm_service(llm_provider)
            answer = llm_service.generate(
                prompt=f"Question: {question}",
                system_prompt=self._get_system_prompt(context)
            )

            # Build sources
            sources = []
            if include_sources:
                sources = self._build_sources(search_results)

            # Get unique doc IDs used
            doc_ids_used = list(set(r.doc_id for r in search_results))

            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"Query completed: {len(search_results)} results, "
                f"{len(doc_ids_used)} docs, {processing_time:.2f}ms"
            )

            return {
                "answer": answer,
                "sources": sources,
                "doc_ids_used": doc_ids_used,
                "processing_time_ms": processing_time,
                "metadata": {
                    "num_results": len(search_results),
                    "llm_provider": llm_provider or settings.DEFAULT_LLM_PROVIDER.value
                }
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def compare_documents(
        self,
        question: str,
        doc_ids: List[str],
        session_id: str,
        llm_provider: str = None
    ) -> Dict[str, Any]:
        """
        Compare how different documents answer the same question
        
        Args:
            question: Question to ask each document
            doc_ids: List of document IDs to compare
            session_id: Session ID
            llm_provider: Which LLM to use
        
        Returns:
            Dict with comparisons and summary
        """
        start_time = time.time()

        try:
            comparisons = []

            # Query each document individually
            for doc_id in doc_ids:
                doc_meta = self.document_service.get_document_metadata(doc_id)
                if not doc_meta:
                    continue

                # Verify session ownership
                if doc_meta.session_id != session_id:
                    logger.warning(f"Session {session_id} not authorized for doc {doc_id}")
                    continue

                # Query this document
                result = await self.query_documents(
                    question=question,
                    session_id=session_id,
                    doc_ids=[doc_id],
                    llm_provider=llm_provider,
                    top_k=3,
                    include_sources=True
                )

                comparisons.append({
                    "doc_id": doc_id,
                    "filename": doc_meta.filename,
                    "answer": result["answer"],
                    "sources": result["sources"][:2]  # Limit sources
                })

            # Generate comparative summary
            llm_service = get_llm_service(llm_provider)
            summary = self._generate_comparison_summary(question, comparisons, llm_service)

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"Comparison completed: {len(comparisons)} documents, {processing_time:.2f}ms")

            return {
                "question": question,
                "comparisons": comparisons,
                "summary": summary,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            raise

    def _build_context(self, search_results: List[SearchResult]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            doc_meta = self.document_service.get_document_metadata(result.doc_id)
            filename = doc_meta.filename if doc_meta else "Unknown"
            
            page_info = f" (Page {result.page_num})" if result.page_num else ""
            
            context_parts.append(
                f"[Source {i} - {filename}{page_info}]\n{result.text}"
            )
        
        return "\n\n".join(context_parts)

    def _get_system_prompt(self, context: str) -> str:
        """Generate system prompt with context"""
        return f"""You are a helpful AI assistant that answers questions based on provided document excerpts.

CONTEXT FROM DOCUMENTS:
{context}

INSTRUCTIONS:
- Answer the question based ONLY on the information provided in the context above
- If the context doesn't contain enough information to answer fully, say so
- Be specific and cite which source(s) you're using in your answer
- If multiple sources provide different information, acknowledge the differences
- Keep your answer clear and concise"""

    def _build_sources(self, search_results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Build sources list from search results"""
        sources = []
        
        for result in search_results:
            doc_meta = self.document_service.get_document_metadata(result.doc_id)
            
            sources.append({
                "doc_id": result.doc_id,
                "filename": doc_meta.filename if doc_meta else "Unknown",
                "chunk_id": result.chunk_id,
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "page_num": result.page_num,
                "score": result.score
            })
        
        return sources

    def _generate_comparison_summary(
        self,
        question: str,
        comparisons: List[Dict[str, Any]],
        llm_service
    ) -> str:
        """Generate a summary comparing answers from different documents"""
        
        comparison_text = f"Question: {question}\n\n"
        for comp in comparisons:
            comparison_text += f"Document '{comp['filename']}':\n{comp['answer']}\n\n"

        prompt = f"""Compare how different documents answer the same question:

{comparison_text}

Provide a brief summary highlighting:
1. Common themes across documents
2. Key differences or contradictions
3. Which document(s) provide the most comprehensive answer

Keep your summary concise (3-4 sentences)."""

        return llm_service.generate(prompt)


# Global instance
_query_service = None

def get_query_service() -> QueryService:
    """Get or create global query service instance"""
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service
