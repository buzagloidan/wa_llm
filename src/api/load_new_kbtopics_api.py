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
