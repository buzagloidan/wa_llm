import logging
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from load_new_kbtopics import topicsLoader
from whatsapp import WhatsAppClient
from voyageai.client_async import AsyncClient
from .deps import get_db_async_session, get_whatsapp, get_text_embebedding

router = APIRouter()

# Configure logger for this module
logger = logging.getLogger(__name__)


from pydantic import BaseModel
from typing import List

class DocumentUpload(BaseModel):
    title: str
    content: str
    source: str = "manual_upload"

@router.post("/load_company_documentation")
async def load_company_documentation_api(
    documents: List[DocumentUpload],
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    embedding_client: Annotated[AsyncClient, Depends(get_text_embebedding)],
) -> Dict[str, Any]:
    """
    Load company documentation into the knowledge base.
    Accepts a list of documents with title, content, and optional source.
    Returns a success message upon completion.
    """
    try:
        logger.info(f"Loading {len(documents)} company documents via API")

        from load_new_kbtopics import CompanyDocumentLoader
        doc_loader = CompanyDocumentLoader()
        loaded_count = await doc_loader.load_documents(
            session, embedding_client, documents
        )

        logger.info(f"Company documentation loading completed successfully. Loaded {loaded_count} documents.")

        return {
            "status": "success",
            "message": f"Successfully loaded {loaded_count} company documents into knowledge base",
            "documents_processed": loaded_count
        }

    except Exception as e:
        logger.error(f"Error during company documentation loading: {str(e)}")
        # Re-raise the exception to let FastAPI handle it with proper error response
        raise

@router.post("/process_all_documentation")
async def process_all_documentation_api(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    embedding_client: Annotated[AsyncClient, Depends(get_text_embebedding)],
) -> Dict[str, Any]:
    """
    Process all documents from the /documentation folder and upload to knowledge base.
    Extracts content from .docx, .pdf, .txt, and .md files.
    """
    try:
        logger.info("Starting processing of all documentation files...")

        from document_processor import process_and_upload_documents
        
        # Process and upload all documents
        loaded_count = await process_and_upload_documents(
            embedding_client, session, "documentation"
        )

        logger.info(f"Documentation processing completed. Loaded {loaded_count} documents.")

        return {
            "status": "success",
            "message": f"Successfully processed and loaded {loaded_count} documents from /documentation folder",
            "documents_processed": loaded_count,
            "source_directory": "documentation/",
            "supported_formats": [".docx", ".pdf", ".txt", ".md"]
        }

    except ImportError as e:
        logger.error(f"Missing required libraries: {e}")
        return {
            "status": "error",
            "message": f"Missing required libraries for document processing: {str(e)}",
            "suggestion": "Install required packages: pip install python-docx PyPDF2"
        }
    except Exception as e:
        logger.error(f"Error during documentation processing: {str(e)}")
        # Re-raise the exception to let FastAPI handle it with proper error response
        raise
