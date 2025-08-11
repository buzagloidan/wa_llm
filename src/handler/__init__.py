import logging
import httpx

from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.router import Router
from handler.whatsapp_group_link_spam import WhatsappGroupLinkSpamHandler
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
        self.whatsapp_group_link_spam = WhatsappGroupLinkSpamHandler(
            session, whatsapp, embedding_client
        )
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        if (
            message
            and message.group
            and message.group.managed
            and message.group.forward_url
        ):
            await self.forward_message(payload, message.group.forward_url)

        # ignore messages that don't exist or don't have text
        if not message or not message.text:
            return

        if message.sender_jid.endswith("@lid"):
            logging.info(
                f"Received message from {message.sender_jid}: {payload.model_dump_json()}"
            )

        # ignore messages from unmanaged groups
        if message and message.group and not message.group.managed:
            logger.info(f"Ignoring message from unmanaged group: {message.group_jid}")
            return
        
        if message and message.group:
            logger.info(f"Processing message from managed group: {message.group_jid}, managed={message.group.managed}")

        bot_jid = await self.whatsapp.get_my_jid()
        is_mentioned = message.has_mentioned(bot_jid)
        logger.info(f"Bot mention check - Group: {message.group_jid}, Bot JID: {bot_jid}, Bot User: {bot_jid.user}, Message: {message.text[:100]}..., Is Mentioned: {is_mentioned}")
        
        if is_mentioned:
            await self.router(message)

        # Handle whatsapp links in group
        if (
            message.group
            and message.group.managed
            and message.group.notify_on_spam
            and "https://chat.whatsapp.com/" in message.text
        ):
            await self.whatsapp_group_link_spam(message)

    async def forward_message(
        self, payload: WhatsAppWebhookPayload, forward_url: str
    ) -> None:
        """
        Forward a message to the group's configured forward URL using HTTP POST.

        :param payload: The WhatsApp webhook payload to forward
        :param forward_url: The URL to forward the message to
        """
        # Ensure we have a forward URL
        if not forward_url:
            return

        try:
            # Create an async HTTP client and forward the message
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    forward_url,
                    json=payload.model_dump(mode="json"),  # Convert Pydantic model to dict for JSON serialization
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

        except httpx.HTTPError as exc:
            # Log the error but don't raise it to avoid breaking message processing
            logger.error(f"Failed to forward message to {forward_url}: {exc}")
        except Exception as exc:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error forwarding message to {forward_url}: {exc}")
