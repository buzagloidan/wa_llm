import logging
import httpx

from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.router import Router
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class MessageHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.router = Router(session, whatsapp, embedding_client)
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        # Only process private messages with text content
        if not message or not message.text:
            logger.info("Ignoring message without text content")
            return

        # Check if message is from a group - we only handle private messages now
        from whatsapp.jid import parse_jid
        chat_jid = parse_jid(message.chat_jid)
        if chat_jid.is_group():
            logger.info(f"Ignoring group message from {message.chat_jid}")
            return

        logger.info(f"Processing private message from {message.sender_jid}: {message.text[:100]}...")

        # Process all private messages - no need to check for mentions since it's a private chat
        await self.router(message)
