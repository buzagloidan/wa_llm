from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import ValidationError
from starlette.requests import ClientDisconnect

from api.deps import get_handler
from handler import MessageHandler
from models.webhook import WhatsAppWebhookPayload

# Create router for webhook endpoints
router = APIRouter(tags=["webhook"])


import logging

logger = logging.getLogger(__name__)

@router.get("/webhook")
async def webhook_health() -> dict:
    """Health check endpoint for webhook"""
    logger.info("Webhook health check accessed")
    return {"status": "ok", "message": "Webhook is accessible"}

@router.post("/webhook")
async def webhook(
    request: Request,
    handler: Annotated[MessageHandler, Depends(get_handler)],
) -> str:
    """
    WhatsApp webhook endpoint for receiving incoming messages.
    Returns:
        Simple "ok" response to acknowledge receipt
    """
    raw_body = None
    try:
        # Get raw JSON first for logging
        raw_body = await request.body()
        logger.info(f"Raw webhook received: {raw_body.decode()[:500]}...")
        
        # Parse JSON manually first
        import json
        raw_json = json.loads(raw_body)
        logger.info(f"Parsed JSON keys: {list(raw_json.keys())}")
        
        # Now try to validate with Pydantic
        payload = WhatsAppWebhookPayload.model_validate(raw_json)
        
        logger.info(f"Webhook validated - From: {payload.from_}, Message ID: {getattr(payload.message, 'id', 'N/A') if payload.message else 'No message'}, Text: {getattr(payload.message, 'text', 'N/A')[:100] if payload.message else 'No message'}...")
        
        # Only process messages that have a sender (from_ field)
        if payload.from_:
            logger.info(f"Processing message from {payload.from_}")
            await handler(payload)
        else:
            logger.warning("Webhook payload missing from_ field, skipping processing")

        return "ok"
        
    except ClientDisconnect:
        logger.warning("Client disconnected during webhook processing")
        return "ok"  # Still return ok to avoid webhook retries
    except ValidationError as e:
        logger.error(f"Webhook validation error: {e}")
        if raw_body:
            logger.error(f"Raw body that failed validation: {raw_body.decode()}")
        return "ok"  # Still return ok to avoid webhook retries
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        if raw_body:
            logger.error(f"Raw body: {raw_body.decode()}")
        return "ok"  # Still return ok to avoid webhook retries
