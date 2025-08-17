import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.knowledge_base_answers import KnowledgeBaseAnswers
from models import Message
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler

# Creating an object
logger = logging.getLogger(__name__)


class Router(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.ask_knowledge_base = KnowledgeBaseAnswers(
            session, whatsapp, embedding_client
        )
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, message: Message):
        # Send immediate emoji reaction to acknowledge message receipt
        try:
            await self.whatsapp.react_to_message(
                message_id=message.message_id,
                phone=message.chat_jid,
                emoji="💬"
            )
            logger.info(f"Sent immediate reaction 💬 for message {message.message_id}")
        except Exception as e:
            logger.warning(f"Failed to send immediate reaction: {e}")
        
        # Route all intents to LLM knowledge base for intelligent responses
        await self.ask_knowledge_base(message)


