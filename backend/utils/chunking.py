# backend/utils/chunking.py
from typing import List, Dict, Any
from enum import Enum
import re
import logging

from config import get_settings, ChunkingStrategy
from models import ChunkMetadata

logger = logging.getLogger(__name__)
settings = get_settings()


class TextChunker:
    """Advanced text chunking with multiple strategies"""

    def __init__(
        self,
        strategy: ChunkingStrategy = None,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.strategy = strategy or settings.CHUNKING_STRATEGY
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_text(
        self,
        text: str,
        doc_id: str,
        page_nums: List[int] = None
    ) -> List[ChunkMetadata]:
        """
        Chunk text using the specified strategy
        
        Args:
            text: The text to chunk
            doc_id: Document ID for metadata
            page_nums: Optional list of page numbers corresponding to text sections
        
        Returns:
            List of ChunkMetadata objects
        """
        if self.strategy == ChunkingStrategy.FIXED:
            return self._fixed_size_chunking(text, doc_id, page_nums)
        elif self.strategy == ChunkingStrategy.RECURSIVE:
            return self._recursive_chunking(text, doc_id, page_nums)
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            return self._semantic_chunking(text, doc_id, page_nums)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

    def _fixed_size_chunking(
        self,
        text: str,
        doc_id: str,
        page_nums: List[int] = None
    ) -> List[ChunkMetadata]:
        """Simple fixed-size chunking with overlap"""
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            if not chunk_text.strip():
                break

            chunks.append(ChunkMetadata(
                chunk_id=f"{doc_id}_chunk_{chunk_index}",
                doc_id=doc_id,
                page_num=page_nums[chunk_index] if page_nums and chunk_index < len(page_nums) else None,
                chunk_index=chunk_index,
                text=chunk_text,
                char_count=len(chunk_text),
                token_count=self._estimate_tokens(chunk_text)
            ))

            start = end - self.chunk_overlap
            chunk_index += 1

        logger.info(f"Fixed chunking: created {len(chunks)} chunks")
        return chunks

    def _recursive_chunking(
        self,
        text: str,
        doc_id: str,
        page_nums: List[int] = None
    ) -> List[ChunkMetadata]:
        """
        Recursive chunking that respects document structure
        Tries to split on: paragraphs -> sentences -> words
        """
        separators = [
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            "! ",
            "? ",
            " ",     # Words
            ""       # Characters (last resort)
        ]

        chunks = self._recursive_split(text, separators, 0)
        
        # Convert to ChunkMetadata
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append(ChunkMetadata(
                chunk_id=f"{doc_id}_chunk_{i}",
                doc_id=doc_id,
                page_num=page_nums[i] if page_nums and i < len(page_nums) else None,
                chunk_index=i,
                text=chunk,
                char_count=len(chunk),
                token_count=self._estimate_tokens(chunk)
            ))

        logger.info(f"Recursive chunking: created {len(chunk_metadata)} chunks")
        return chunk_metadata

    def _recursive_split(
        self,
        text: str,
        separators: List[str],
        sep_index: int
    ) -> List[str]:
        """Recursively split text using hierarchical separators"""
        if sep_index >= len(separators):
            return [text]

        separator = separators[sep_index]
        splits = text.split(separator) if separator else list(text)

        chunks = []
        current_chunk = ""

        for split in splits:
            # Add separator back (except for empty separator)
            split_with_sep = split + separator if separator else split

            if len(current_chunk) + len(split_with_sep) <= self.chunk_size:
                current_chunk += split_with_sep
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if len(split_with_sep) > self.chunk_size:
                    # Split further using next separator
                    sub_chunks = self._recursive_split(split_with_sep, separators, sep_index + 1)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split_with_sep

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _semantic_chunking(
        self,
        text: str,
        doc_id: str,
        page_nums: List[int] = None
    ) -> List[ChunkMetadata]:
        """
        Semantic chunking based on topic/meaning
        For now, uses paragraph-based chunking with semantic boundaries
        (Full semantic chunking would require embeddings)
        """
        # Split on double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding paragraph exceeds size, save current and start new
            if current_chunk and len(current_chunk) + len(para) > self.chunk_size:
                chunks.append(ChunkMetadata(
                    chunk_id=f"{doc_id}_chunk_{chunk_index}",
                    doc_id=doc_id,
                    page_num=page_nums[chunk_index] if page_nums and chunk_index < len(page_nums) else None,
                    chunk_index=chunk_index,
                    text=current_chunk.strip(),
                    char_count=len(current_chunk),
                    token_count=self._estimate_tokens(current_chunk)
                ))
                chunk_index += 1
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"

        # Add final chunk
        if current_chunk.strip():
            chunks.append(ChunkMetadata(
                chunk_id=f"{doc_id}_chunk_{chunk_index}",
                doc_id=doc_id,
                page_num=page_nums[chunk_index] if page_nums and chunk_index < len(page_nums) else None,
                chunk_index=chunk_index,
                text=current_chunk.strip(),
                char_count=len(current_chunk),
                token_count=self._estimate_tokens(current_chunk)
            ))

        logger.info(f"Semantic chunking: created {len(chunks)} chunks")
        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(text) // 4


def chunk_document(
    text: str,
    doc_id: str,
    strategy: ChunkingStrategy = None,
    chunk_size: int = None,
    chunk_overlap: int = None,
    page_nums: List[int] = None
) -> List[ChunkMetadata]:
    """
    Convenience function to chunk a document
    
    Args:
        text: The text to chunk
        doc_id: Document ID
        strategy: Chunking strategy to use
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        page_nums: Optional page numbers
    
    Returns:
        List of ChunkMetadata objects
    """
    chunker = TextChunker(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_text(text, doc_id, page_nums)
