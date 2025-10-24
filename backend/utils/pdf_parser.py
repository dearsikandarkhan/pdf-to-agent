# backend/utils/pdf_parser.py
from typing import Tuple, List, Dict, Any
import logging
from datetime import datetime
import io

logger = logging.getLogger(__name__)


class PDFParseError(Exception):
    """Custom exception for PDF parsing errors"""
    pass


class PDFParser:
    """Enhanced PDF parser with error handling and metadata extraction"""

    def __init__(self):
        try:
            from PyPDF2 import PdfReader
            self.PdfReader = PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

    def parse_pdf(
        self,
        content: bytes,
        filename: str = "unknown.pdf"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Parse PDF and extract text + metadata
        
        Args:
            content: PDF file content as bytes
            filename: Original filename
        
        Returns:
            Tuple of (extracted_text, metadata_dict)
        
        Raises:
            PDFParseError: If PDF parsing fails
        """
        try:
            # Create PDF reader from bytes
            pdf_file = io.BytesIO(content)
            reader = self.PdfReader(pdf_file)

            # Extract metadata
            metadata = self._extract_metadata(reader, filename, len(content))

            # Extract text from all pages
            text_by_page = []
            page_numbers = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_by_page.append(page_text)
                        page_numbers.append(page_num + 1)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue

            if not text_by_page:
                raise PDFParseError("No text could be extracted from the PDF")

            # Combine all text
            full_text = "\n\n".join(text_by_page)

            # Add page mapping to metadata
            metadata["page_numbers"] = page_numbers
            metadata["text_extracted_pages"] = len(text_by_page)

            logger.info(
                f"Successfully parsed PDF '{filename}': "
                f"{len(reader.pages)} pages, {len(full_text)} characters"
            )

            return full_text, metadata

        except PDFParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF '{filename}': {e}")
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")

    def _extract_metadata(
        self,
        reader,
        filename: str,
        file_size: int
    ) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = {
            "filename": filename,
            "file_size": file_size,
            "num_pages": len(reader.pages),
            "parse_timestamp": datetime.now().isoformat()
        }

        # Try to get PDF metadata
        try:
            if reader.metadata:
                pdf_meta = reader.metadata
                metadata.update({
                    "title": pdf_meta.get("/Title", ""),
                    "author": pdf_meta.get("/Author", ""),
                    "subject": pdf_meta.get("/Subject", ""),
                    "creator": pdf_meta.get("/Creator", ""),
                    "producer": pdf_meta.get("/Producer", ""),
                    "creation_date": pdf_meta.get("/CreationDate", ""),
                })
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata: {e}")

        return metadata

    def validate_pdf(self, content: bytes) -> Tuple[bool, str]:
        """
        Validate if content is a valid PDF
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            pdf_file = io.BytesIO(content)
            reader = self.PdfReader(pdf_file)
            
            # Try to access first page
            if len(reader.pages) == 0:
                return False, "PDF has no pages"
            
            # Try to extract text from first page
            _ = reader.pages[0].extract_text()
            
            return True, ""
        except Exception as e:
            return False, str(e)


def parse_pdf_content(content: bytes, filename: str = "unknown.pdf") -> Tuple[str, Dict[str, Any]]:
    """
    Convenience function to parse PDF content
    
    Args:
        content: PDF file bytes
        filename: Original filename
    
    Returns:
        Tuple of (text, metadata)
    """
    parser = PDFParser()
    return parser.parse_pdf(content, filename)


def validate_pdf_content(content: bytes) -> Tuple[bool, str]:
    """
    Convenience function to validate PDF
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    parser = PDFParser()
    return parser.validate_pdf(content)
