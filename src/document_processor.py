#!/usr/bin/env python3
"""
Document processor for extracting content from various file formats
and preparing them for embedding in the knowledge base.
"""
import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

# Document processing libraries
try:
    import docx  # python-docx for .docx files
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2  # PyPDF2 for .pdf files
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process various document formats and extract text content."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.docx', '.pdf'}
    
    def __init__(self, docs_directory: str = "documentation"):
        self.docs_directory = Path(docs_directory)
        
    def extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX files."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")
            
        try:
            doc = docx.Document(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF files."""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available. Install with: pip install PyPDF2")
            
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT/MD files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                return ""
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """Extract text from any supported file format."""
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.docx':
                return self.extract_text_from_docx(file_path)
            elif extension == '.pdf':
                return self.extract_text_from_pdf(file_path)
            elif extension in {'.txt', '.md'}:
                return self.extract_text_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file format: {extension}")
                return None
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return None
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """Process all documents in the documentation directory."""
        documents = []
        
        if not self.docs_directory.exists():
            logger.error(f"Documentation directory not found: {self.docs_directory}")
            return []
        
        logger.info(f"Processing documents from: {self.docs_directory}")
        
        for file_path in self.docs_directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                logger.info(f"Processing: {file_path}")
                
                # Extract text content
                content = self.extract_text_from_file(file_path)
                
                if content and content.strip():
                    # Create document object
                    doc = {
                        "title": file_path.stem,  # Filename without extension
                        "content": content.strip(),
                        "source": f"documentation/{file_path.relative_to(self.docs_directory)}",
                        "file_type": file_path.suffix.lower(),
                        "file_size": file_path.stat().st_size,
                        "processed_at": datetime.now().isoformat()
                    }
                    
                    documents.append(doc)
                    logger.info(f"Processed {file_path.name}: {len(content)} characters")
                else:
                    logger.warning(f"No content extracted from {file_path}")
        
        logger.info(f"Successfully processed {len(documents)} documents")
        return documents

class JeenDocumentProcessor(DocumentProcessor):
    """Specialized document processor for Jeen.ai documentation."""
    
    def clean_jeen_content(self, content: str) -> str:
        """Clean and normalize Jeen.ai specific content."""
        # Remove excessive whitespace
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with single newlines
        cleaned = '\n'.join(lines)
        
        # Replace multiple spaces with single spaces
        import re
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned
    
    def extract_jeen_sections(self, content: str, title: str) -> List[Dict[str, Any]]:
        """Extract logical sections from Jeen.ai documentation."""
        # For now, treat each document as one section
        # This can be enhanced to split documents into logical sections
        
        return [{
            "title": f"Jeen.ai Guide: {title}",
            "content": self.clean_jeen_content(content),
            "source": "jeen_documentation",
            "category": self.categorize_jeen_document(title)
        }]
    
    def categorize_jeen_document(self, title: str) -> str:
        """Categorize Jeen.ai documents based on title."""
        title_lower = title.lower()
        
        if 'chat' in title_lower:
            return 'chat_features'
        elif 'interactive' in title_lower:
            return 'interactive_features'
        elif 'workflow' in title_lower:
            return 'workflow_features'
        elif 'admin' in title_lower:
            return 'administration'
        elif 'basic' in title_lower or 'getting started' in title_lower:
            return 'getting_started'
        else:
            return 'general'
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """Process all Jeen.ai documents with specialized handling."""
        documents = []
        
        if not self.docs_directory.exists():
            logger.error(f"Documentation directory not found: {self.docs_directory}")
            return []
        
        logger.info(f"Processing Jeen.ai documents from: {self.docs_directory}")
        
        for file_path in self.docs_directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                logger.info(f"Processing Jeen.ai doc: {file_path}")
                
                # Extract text content
                content = self.extract_text_from_file(file_path)
                
                if content and content.strip():
                    # Extract sections from this document
                    sections = self.extract_jeen_sections(content, file_path.stem)
                    
                    for section in sections:
                        doc = {
                            "title": section["title"],
                            "content": section["content"],
                            "source": f"jeen_docs/{file_path.relative_to(self.docs_directory)}",
                            "category": section["category"],
                            "file_type": file_path.suffix.lower(),
                            "original_file": str(file_path.relative_to(self.docs_directory)),
                            "processed_at": datetime.now().isoformat()
                        }
                        
                        documents.append(doc)
                        logger.info(f"Processed Jeen.ai section: {section['title']}")
                else:
                    logger.warning(f"No content extracted from {file_path}")
        
        logger.info(f"Successfully processed {len(documents)} Jeen.ai document sections")
        return documents

async def process_and_upload_documents(
    embedding_client, 
    session, 
    docs_directory: str = "documentation"
) -> int:
    """Process all documents and upload them to the knowledge base."""
    from load_new_kbtopics import CompanyDocumentLoader
    
    # Process documents
    processor = JeenDocumentProcessor(docs_directory)
    documents = processor.process_all_documents()
    
    if not documents:
        logger.warning("No documents found to process")
        return 0
    
    # Upload to knowledge base
    doc_loader = CompanyDocumentLoader()
    loaded_count = await doc_loader.load_documents(
        session, embedding_client, documents
    )
    
    logger.info(f"Successfully uploaded {loaded_count} document sections to knowledge base")
    return loaded_count